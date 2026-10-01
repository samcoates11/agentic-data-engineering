# Sanity check that local AWS credentials resolve via boto3's default
# credential chain (env vars, ~/.aws/credentials, SSO, or an assumed role).
import boto3

session = boto3.Session()
print("Account identity:")
sts = session.client("sts")
print(sts.get_caller_identity())