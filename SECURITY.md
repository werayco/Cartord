# Security Policy

## Supported versions

This project is under active development. Security fixes are prioritized for the current main branch and the most recent release line available in the repository.

## Reporting a vulnerability

If you discover a security issue in Cartord, please do not open a public issue or discussion. Instead, report it privately using one of the following options:

- Open a private security advisory through the repository's GitHub Security tab if available
- Contact the project maintainer directly through the repository owner contact details
- Use the repository's private reporting channel, if one is configured

Please include as much detail as possible:

- Summary of the vulnerability and affected component
- Steps to reproduce or exploit it
- Impact assessment and severity
- Relevant logs, requests, or proof-of-concept material
- Your preferred contact method for follow-up

## Response expectations

We aim to acknowledge new reports promptly and work toward a fix as quickly as possible. Depending on the severity and scope, we may ask for additional information or coordinate disclosure timing.

## Disclosure policy

We ask researchers and contributors to give maintainers a reasonable opportunity to investigate and patch the issue before public disclosure. If a fix is ready, we will coordinate a responsible disclosure timeline with the reporter where appropriate.

## Security best practices

When working with this project locally or in deployment environments:

- Keep dependencies and container images updated
- Use least-privilege credentials and secrets management
- Restrict network access to internal service boundaries
- Review logs and monitoring for unusual behavior in Kafka, Postgres, and service APIs
- Treat all credentials, tokens, and customer data as sensitive

## Scope

This policy applies to the Cartord repository, its deployment configuration, and service-level security issues discovered in the project as maintained here.
