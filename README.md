# About

When managing a large number of AWS Accounts in an Organization we put account security at highest priority. To monitor IAM credentials AWS provides a credential report which is a used for security and compliance purposes. It provides detailed information about the status and configuration of the AWS credentials associated with an AWS account. The report includes information about the access keys and IAM (Identity and Access Management) users, their creation dates, last usage dates, and other relevant details.

The credential report is essential for several reasons:

- `Security`: It helps identify and assess potential security risks associated with AWS credentials. By reviewing the report, administrators can identify unused or dormant credentials that may pose a security threat if they fall into the wrong hands. It enables organizations to monitor and manage access to AWS resources effectively.

- `Compliance`: Many organizations need to comply with various regulatory requirements and industry standards, such as the Payment Card Industry Data Security Standard (PCI DSS) or the General Data Protection Regulation (GDPR). The credential report allows organizations to demonstrate compliance by providing an audit trail of the AWS credentials and their usage.

- `Access Management`: The report provides insights into the status of IAM users and access keys. It helps administrators identify users with excessive privileges, detect unused or expired credentials, and ensure appropriate access controls are in place. This information is valuable for maintaining a well-managed and secure AWS environment.

- `Monitoring and Troubleshooting`: The credential report assists in monitoring and troubleshooting access-related issues. Administrators can review the report to investigate access problems, track the usage of access keys, and identify potential misconfigurations or policy violations.

## Why do I need this?

We can pull credential report manually if it is for 2-3 AWS accounts we maintain, however in a scenario where we manage 100 or more AWS accounts it is no longer feasible to do it manually and that is where we need automation to chime in and solve the problem. 
This lambda function runs in the master account in an AWS Org and scans all the child accounts for their credential report. It then adds all these individual report in a single csv file which can either be referenced locally or scheduled via Event Bridge / SES to designated emails. 

## Local Implementation  

- Make sure you have `Python` installed.
- Make sure the AWS Master management account has visibility to all the child accounts it maintains using `OrganizationAccountAccessRole`. Ideally it should be present by default. You can read more on it [here](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html)
- Set the AWS credentials in the terminal (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN if running it locally) of the AWS Master Management Account. 
- Run the scripts using the command `python3 lambda_function.py`
- Once the script execution completes the data CSV credential report for all account maintained by the organization is generated in `./credential-report-automation`

## Note 

I have commented out `csv_to_html_notification` function which can be enabled as per the use-case to schedule report delivery through SES and Event Brdige once configured in the AWS Master account.

- Make sure to update `sender` and `receipient` in `lamnda_handler()` function when using `SES`.

```
sender = "<Enter Email Address of the Sender configured in SES>"  
recipient = "<Enter Email Address of the Recepient configured in SES>"
```
- Un-comment `fetchUser.csv_to_html_notification()` in `lambda_handler()` function if you have SES set-up and wanted to use the service for email delivery

The lambda function uses `pandas` - Python Data Analyst Library to convert the `csv` to `html` for sending it via AWS SES. `pandas` libarary is available in-built in AWS Lambda only if `Python 3.9` is selected as runtime.
After selecting the runtime as `Python 3.9` we have to add `Layers` to support `AWSSDKPandas`.

## Authors

- [Ranopriyo Neogy](https://github.com/ranopriyo-neogy)