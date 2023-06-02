import boto3
import time
import csv
import os
import pandas as pd
from datetime import datetime


class FetchUser:
    def __init__(self, sender, recipient, aws_region, file_location, file_name) -> None:
        self.sender = sender
        self.recipient = recipient
        self.aws_region = aws_region
        self.file_location = file_location
        self.file_name = file_name

    def getReport(self, account_id):
        """
        This function is used to generate and fetch the iam credential report
        """
        sts = boto3.client("sts")
        # Assume Role in the child account using OrganizationAccountAccessRole
        assumed_role = sts.assume_role(
            RoleArn=f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole",
            RoleSessionName="AssumeRoleSession",
        )
        # Create an IAM client for the child account
        iam = boto3.client(
            "iam",
            region_name="us-east-1",
            aws_access_key_id=assumed_role["Credentials"]["AccessKeyId"],
            aws_secret_access_key=assumed_role["Credentials"]["SecretAccessKey"],
            aws_session_token=assumed_role["Credentials"]["SessionToken"],
        )
        try:
            # Generate the report in the child account
            response = iam.generate_credential_report()
            print("Report generation has started for: ", account_id)
            time.sleep(2)
        except Exception as e:
            print(
                "generate_credential_report timed out for: ",
                account_id,
                " with Exception: ",
                e,
            )
        try:
            # Get the generated report from the child account
            response = iam.get_credential_report()
            time.sleep(2)
            return response
        except Exception as e:
            print(
                "get_credential_report timed out for: ",
                account_id,
                " with Exception: ",
                e,
            )

    def csv_generator(self, response, flag):
        """
        This function is used to append iam credential report in a single csv file
        """
        try:
            report_csv = response["Content"].decode("utf-8").splitlines()
            report_reader = csv.reader(report_csv)
            # Get the headers from the first row of the report
            headers = next(report_reader)
            file_location = self.file_location
            file_name = self.file_name
            file_path = os.path.join(file_location, file_name)
            with open(file_path, "a", newline="") as csvfile:
                report_writer = csv.writer(csvfile)
                # To check if the execution header is picked for the first time from response
                if flag == "true":
                    # If picked for the first time, write the header to the CSV file
                    report_writer.writerow(headers)
                # Write each row of the report to the CSV file
                for row in report_reader:
                    report_writer.writerow(row)
        except Exception as e:
            print("Exception occured in csv_generator while insertion", e)
            
    ###############################################################################################################################################
    # Enable this if you want to integrate SES service for sending email. Just make sure you have it configured in the account as a pre-requisite.
    ###############################################################################################################################################
    
    # def csv_to_html_notification(self):
    #     """
    #     This function is used to convert the csv generated to html table and pass it to AWS SES service for email notification
    #     """
    #     try:
    #         file_location = self.file_location
    #         file_name = self.file_name
    #         file_path = os.path.join(file_location, file_name)
    #         current_date = datetime.now().strftime("%Y-%m-%d")
    #         # Read the CSV file into a Pandas DataFrame
    #         df = pd.read_csv(file_path)
    #         # Convert the DataFrame to an HTML table
    #         html_table = df.to_html(index=False)
    #         CHARSET = "UTF-8"
    #         SENDER = self.sender
    #         RECIPIENT = self.recipient
    #         AWS_REGION = self.aws_region
    #         SUBJECT = f" Daily AWS Org Credential Report - {current_date}"
    #         BODY_HTML = f""" Credential Report for all accounts in AWS Org on {current_date} : <br><br><br> {html_table}"""
    #         client = boto3.client("ses", region_name=AWS_REGION)
    #         response = client.send_email(
    #             Destination={
    #                 "ToAddresses": [
    #                     RECIPIENT,
    #                 ],
    #             },
    #             Message={
    #                 "Body": {
    #                     "Html": {
    #                         "Charset": CHARSET,
    #                         "Data": BODY_HTML,
    #                     },
    #                 },
    #                 "Subject": {
    #                     "Charset": CHARSET,
    #                     "Data": SUBJECT,
    #                 },
    #             },
    #             Source=SENDER,
    #         )
    #         print(response)
    #     except Exception as e:
    #         print("Exception occured in csv_to_html_notification", e)

    def list_all_accounts(self):
        """
        This function is used to list all accounts in the AWS Org
        """
        try:
            client = boto3.client("organizations")
            accounts = []
            next_token = None
            while True:
                if next_token:
                    response = client.list_accounts(NextToken=next_token)
                else:
                    response = client.list_accounts()
                accounts += response["Accounts"]
                if "NextToken" in response:
                    next_token = response["NextToken"]
                else:
                    break
            return accounts
        except Exception as e:
            print("Exception occured in list_all_accounts function", e)
    
    def deleteExisitingReport(self):
        """
        This deletes any credential_report.csv file present at home (~/) from previous executions
        """
        file_path = f"{self.file_location}/credential_report.csv"
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"{file_path} successfully deleted.")
            else:
                print(f"{file_path} not found or this is first time you executed the code")
        except OSError as e:
            print(f"Error: {file_path} could not be deleted / not-present. {e}")


def lambda_handler():
    flag = "true" 
    sender = "<Enter Email Address of the Sender configured in SES>"  
    recipient = "<Enter Email Address of the Recepient configured in SES>"
    aws_region = "us-east-1"
    current_directory = os.getcwd()
    file_location = current_directory
    file_name = "credential_report.csv"
    try:
        """
        If you plan to use SES for email notification, please send sender and recipient arguments to FetchUser() function along with aws_region, file_location, file_name. 
        """
        fetchUser = FetchUser(sender, recipient,aws_region, file_location, file_name)
        fetchUser.deleteExisitingReport()
        accounts = fetchUser.list_all_accounts()
        time.sleep(10)
        for account in accounts:
            account_id = account["Id"]
            status = account["Status"]
            if (
                status == "ACTIVE"
            ):
                response = fetchUser.getReport(account_id)
                if response is not None:
                    fetchUser.csv_generator(response, flag)
                    flag = "false"
                else:
                    print("Response is null in lambda_handler for: ", account_id)
        """
        Un-comment below fetchUser.csv_to_html_notification() if you have SES set-up and wanted to use the service for email delivery
        """
        # fetchUser.csv_to_html_notification()
        print(f"Scan completed - Report stored at - {file_location}/credential_report.csv")
    except Exception as e:
        print("Exception occured in lambda_handler function: ", e)
lambda_handler()