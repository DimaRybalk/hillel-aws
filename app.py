#!/usr/bin/env python3
import aws_cdk as cdk
from short_urls.short_urls_stack import ShortUrlsStack

app = cdk.App()
student = app.node.try_get_context("student")

if not student:
    raise ValueError("Потрібно передати контекст студента: cdk deploy -c student=<прізвище>")

ShortUrlsStack(app, f"short-urls-{student}", student=student)

app.synth()