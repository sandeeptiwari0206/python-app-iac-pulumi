"""
Pulumi Python — creates VPC, EKS Cluster, Node Group, ECR repos.
Equivalent to your eks-cluster.yaml CloudFormation template.
"""

import pulumi
import pulumi_aws as aws

# ---------------------------
# CONFIGURATION (edit these)
# ---------------------------
CLUSTER_NAME = "python-app-cluster"
REGION = "ap-south-1"  # Mumbai
K8S_VERSION = "1.29"

NODE_TYPE = "t3.medium"
NODE_MIN, NODE_MAX, NODE_DESIRED = 1, 4, 2

# ---------------------------
# 1. VPC
# ---------------------------
vpc = aws.ec2.Vpc(f"{CLUSTER_NAME}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": f"{CLUSTER_NAME}-vpc"},
)

# ---------------------------
# 2. INTERNET GATEWAY
# ---------------------------
igw = aws.ec2.InternetGateway(f"{CLUSTER_NAME}-igw",
    vpc_id=vpc.id,
    tags={"Name": f"{CLUSTER_NAME}-igw"},
)

# ---------------------------
# 3. SUBNETS
# ---------------------------
azs = aws.get_availability_zones(state='available')

subnet1 = aws.ec2.Subnet(f"{CLUSTER_NAME}-subnet-1",
    vpc_id=vpc.id,
    cidr_block='10.0.1.0/24',
    availability_zone=azs.names[0],
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{CLUSTER_NAME}-public-subnet-1",
        f"kubernetes.io/cluster/{CLUSTER_NAME}": "shared",
        "kubernetes.io/role/elb": "1",
    },
)

subnet2 = aws.ec2.Subnet(f"{CLUSTER_NAME}-subnet-2",
    vpc_id=vpc.id,
    cidr_block='10.0.2.0/24',
    availability_zone=azs.names[1],
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{CLUSTER_NAME}-public-subnet-2",
        f"kubernetes.io/cluster/{CLUSTER_NAME}": "shared",
        "kubernetes.io/role/elb": "1",
    },
)

# ---------------------------
# 4. ROUTE TABLE
# ---------------------------
rt = aws.ec2.RouteTable(f"{CLUSTER_NAME}-rt",
    vpc_id=vpc.id,
    routes=[aws.ec2.RouteTableRouteArgs(
        cidr_block='0.0.0.0/0',
        gateway_id=igw.id
    )],
    tags={"Name": f"{CLUSTER_NAME}-public-rt"},
)

aws.ec2.RouteTableAssociation(f"{CLUSTER_NAME}-rta-1",
    subnet_id=subnet1.id,
    route_table_id=rt.id
)

aws.ec2.RouteTableAssociation(f"{CLUSTER_NAME}-rta-2",
    subnet_id=subnet2.id,
    route_table_id=rt.id
)

# ---------------------------
# 5. SECURITY GROUP
# ---------------------------
sg = aws.ec2.SecurityGroup(f"{CLUSTER_NAME}-control-plane-sg",
    vpc_id=vpc.id,
    description="EKS Control Plane Security Group",
    tags={"Name": f"{CLUSTER_NAME}-control-plane-sg"},
)

# ---------------------------
# 6. IAM ROLE — EKS CLUSTER
# ---------------------------
cluster_role = aws.iam.Role(f"{CLUSTER_NAME}-cluster-role",
    assume_role_policy="""{
        "Version":"2012-10-17",
        "Statement":[{
            "Effect":"Allow",
            "Principal":{"Service":"eks.amazonaws.com"},
            "Action":"sts:AssumeRole"
        }]
    }"""
)

aws.iam.RolePolicyAttachment(f"{CLUSTER_NAME}-cluster-policy",
    role=cluster_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
)

# ---------------------------
# 7. IAM ROLE — WORKER NODES
# ---------------------------
node_role = aws.iam.Role(f"{CLUSTER_NAME}-node-role",
    assume_role_policy="""{
        "Version":"2012-10-17",
        "Statement":[{
            "Effect":"Allow",
            "Principal":{"Service":"ec2.amazonaws.com"},
            "Action":"sts:AssumeRole"
        }]
    }"""
)

for arn in [
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
]:
    aws.iam.RolePolicyAttachment(f"{CLUSTER_NAME}-{arn.split('/')[-1]}",
        role=node_role.name,
        policy_arn=arn
    )

# ---------------------------
# 8. EKS CLUSTER
# ---------------------------
cluster = aws.eks.Cluster(CLUSTER_NAME,
    name=CLUSTER_NAME,
    version=K8S_VERSION,
    role_arn=cluster_role.arn,   # ✅ FIXED (missing comma earlier)

    vpc_config=aws.eks.ClusterVpcConfigArgs(
        subnet_ids=[subnet1.id, subnet2.id],
        security_group_ids=[sg.id],
        endpoint_public_access=True,
        endpoint_private_access=False,
    ),

    enabled_cluster_log_types=["api", "audit"],
    tags={"Name": CLUSTER_NAME},
)

# ---------------------------
# 9. NODE GROUP
# ---------------------------
node_group = aws.eks.NodeGroup(f"{CLUSTER_NAME}-nodegroup",
    cluster_name=cluster.name,
    node_group_name=f"{CLUSTER_NAME}-nodegroup",
    node_role_arn=node_role.arn,
    subnet_ids=[subnet1.id, subnet2.id],
    instance_types=[NODE_TYPE],

    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        desired_size=NODE_DESIRED,
        min_size=NODE_MIN,
        max_size=NODE_MAX
    ),

    disk_size=20,
    ami_type="AL2_x86_64",

    opts=pulumi.ResourceOptions(depends_on=[cluster]),
)

# ---------------------------
# 10. ECR REPOSITORIES
# ---------------------------
backend_ecr = aws.ecr.Repository("backend-ecr",
    name="python-app/backend",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True
    )
)

frontend_ecr = aws.ecr.Repository("frontend-ecr",
    name="python-app/frontend",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True
    )
)

# ---------------------------
# OUTPUTS
# ---------------------------
pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export("backend_ecr_url", backend_ecr.repository_url)
pulumi.export("frontend_ecr_url", frontend_ecr.repository_url)
pulumi.export("vpc_id", vpc.id)
