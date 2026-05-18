# Security Policy

SIGMABUS is a working draft for safety-critical, edge-native coordination. Do
not deploy this repository as an autonomous control authority without an
independent hazard analysis, integration review, and physical override path.

## Reporting

Open a private security advisory or contact the repository owner before
publishing vulnerabilities that affect identity, signing, trust calculation,
authority delegation, replay prevention, or control handback.

## Safety Boundaries

- Human override remains inalienable.
- All CM messages are expected to be signed by conformant implementations.
- Messages below the effective trust floor must not be acted on.
- Local configs contain placeholders only; never commit production credentials,
  private keys, vessel identifiers, or operational logs.
