"""Kalshi API request signing (RSA-PSS over timestamp+method+path)."""
import base64
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

KEY_PATH = Path("/home/christian/Prediction-Markets/kalshi_private_key.txt")


def load_private_key():
    with open(KEY_PATH, "rb") as f:
        return serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )


def sign_pss(private_key, message: str) -> str:
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def auth_headers(private_key, key_id: str, method: str, path: str) -> dict:
    """Build the three signed headers Kalshi requires.

    NOTE: path must have query parameters stripped before signing.
    """
    ts_ms = str(int(time.time() * 1000))
    path_no_query = path.split("?")[0]
    msg = ts_ms + method + path_no_query
    sig = sign_pss(private_key, msg)
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": ts_ms,
    }
