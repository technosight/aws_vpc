import boto3
from timer import Timer

STATUS_CODE_SUCCESS = 200

def delete_vcp(vpc_id):

    ec2_resource = boto3.resource('ec2')
    ec2_client = ec2_resource.meta.client
    vpc = ec2_resource.Vpc(vpc_id)

    # delete Internet Gatewayus
    for internet_gateway in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=internet_gateway.id)
        result = internet_gateway.delete()
        assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete Route Table Associations
    for route_table in vpc.route_tables.all():
        for rta in route_table.associations:
            if not rta.main:
                result = rta.delete()
                assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete EC2 Instances
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            result = instance.terminate()
            instance.wait_until_termincated()
            assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete Endpoints
    for endpoint in ec2_client.describe_vpc_endpoints(
        Filters=[{
            'Name': 'vpc-id',
            'Values': [vpc_id]
        }]
    )['VpcEndpoints']:
        result = ec2_client.delete_vpc_endpoints(VpcEndpointIds=[endpoint['VpcEndpointId']])
        assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete Security Groups
    for sec_group in vpc.security_groups.all():
        if sec_group.group_name != 'default':
            result = sec_group.delete()
            assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete VPC peering connections
    for peer_con in ec2_client.describe_vpc_peering_connections(
        Filters=[{
            'Name': 'requester-vpc-info.vpc-id',
            'Values': [vpc_id]
        }]
    )['VpcPeeringConnections']:
        result = ec2_resource.VpcPeeringConnection(peer_con['VpcPeeringConnectionId']).delete()
        assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # delete non-default Network ACLs
    for nacl in vpc.network_acls.all():
        if not nacl.is_default:
            result = nacl.delete()
            assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

    # set Timer for deleting Subnets
    timer = Timer(interval=30, timeout=600)

    # Subnet may have pending dependencies hence there are few attempts to delete it
    num_of_subnets = 1 # non-zero value to start the loop
    while num_of_subnets > 0:
        try:
            for subnet in vpc.subnets.all():

                # delete Network Interfaces
                for interface in subnet.network_interfaces.all():
                    result = interface.delete()
                    assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

                # delete Subnet
                result = subnet.delete()
                assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS

            # find remaining Subnets to remove
            subnet_dict = ec2_client.describe_subnets(
                Filters=[{
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                }]
            )
            num_of_subnets = len(subnet_dict.get('Subnets')) or 0

        except Exception as e:
            timer.wait()

    # delete VPC
    timer = Timer(interval=10, timeout=300)
    vpc_deleted = False
    while not vpc_deleted:
        try:
            result = ec2_client.delete_vpc(VpcId=vpc_id)
            assert result.get('ResponseMetadata').get('HTTPStatusCode') == STATUS_CODE_SUCCESS
            vpc_deleted = True
        except Exception as e:
            timer.wait()