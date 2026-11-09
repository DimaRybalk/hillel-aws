from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
from constructs import Construct

class ShortUrlsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, student: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        table = dynamodb.Table(
            self, f"{student}-UrlsTable",
            table_name=f"{student}-short-urls",
            partition_key=dynamodb.Attribute(name="short_key", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expires_at",
        )

        handler = _lambda.Function(
            self, f"{student}-ShortenerFunc",
            function_name=f"{student}-url-shortener",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="url_shortener.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name
            }
        )

        table.grant_read_write_data(handler)

        api = apigw.LambdaRestApi(
            self, f"{student}-ShortenerApi",
            rest_api_name=f"{student}-shortener-api",
            handler=handler,
            proxy=True
        )

        CfnOutput(self, "ApiUrl", value=api.url)