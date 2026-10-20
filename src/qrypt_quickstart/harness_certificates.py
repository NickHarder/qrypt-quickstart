"""A throwaway certificate authority, so a container can reach the mock as `api-eus.qrypt.com`.

The agent harness's container mode maps Qrypt's host name to the mock on the host. For the agent's
program to call `https://api-eus.qrypt.com/...` unchanged, the mock must present a certificate for
that name from an authority the container trusts. This writes both, valid for one day; the
container's entry point adds the authority to its trust store (`agent-harness/entrypoint.sh`).
The authority signs nothing but this one certificate and is never installed on the host.
"""

import datetime
from pathlib import Path
from typing import Final

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

VALIDITY: Final = datetime.timedelta(days=1)


def write_pem_key(path: Path, private_key: ec.EllipticCurvePrivateKey) -> None:
    """Write a private key as unencrypted PKCS #8 PEM."""
    path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )


def write_authority_and_server_certificate(
    directory: Path, *, host_name: str
) -> tuple[Path, Path, Path]:
    """Write a certificate authority and a server certificate it signs for one host name.

    Args:
        directory: Where the three PEM files go; created if missing.
        host_name: The name the server certificate is for, such as "api-eus.qrypt.com".

    Returns:
        The authority's certificate, the server's certificate and the server's private key.
    """
    directory.mkdir(parents=True, exist_ok=True)
    issued_at = datetime.datetime.now(datetime.UTC)
    authority_key = ec.generate_private_key(ec.SECP256R1())
    authority_name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Qrypt quickstart agent-harness authority")]
    )
    authority_certificate = (
        x509.CertificateBuilder()
        .subject_name(authority_name)
        .issuer_name(authority_name)
        .public_key(authority_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(issued_at)
        .not_valid_after(issued_at + VALIDITY)
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(authority_key.public_key()), critical=False
        )
        .sign(authority_key, hashes.SHA256())
    )
    server_key = ec.generate_private_key(ec.SECP256R1())
    server_certificate = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host_name)]))
        .issuer_name(authority_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(issued_at)
        .not_valid_after(issued_at + VALIDITY)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(host_name)]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(authority_key.public_key()),
            critical=False,
        )
        .sign(authority_key, hashes.SHA256())
    )
    authority_path = directory / "harness-authority.pem"
    certificate_path = directory / "server-certificate.pem"
    private_key_path = directory / "server-private-key.pem"
    authority_path.write_bytes(authority_certificate.public_bytes(serialization.Encoding.PEM))
    certificate_path.write_bytes(server_certificate.public_bytes(serialization.Encoding.PEM))
    write_pem_key(private_key_path, server_key)
    return authority_path, certificate_path, private_key_path
