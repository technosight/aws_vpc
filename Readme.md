## AWS Virtual Private Cloud manipulation with boto3

When this code was written, AWS API didn't have a method for uncoditional deletion of Vitual Private Cloud (VPC). This 
code comes through a sequence of all prerequisites that need to be cleaned up prior to VPC deletion.

The runtime needs to have boto3 [configured](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).