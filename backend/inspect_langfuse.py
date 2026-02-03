import os
from langfuse import Langfuse
import inspect

print("Langfuse version:", getattr(Langfuse, "version", "unknown"))
print("Attributes of Langfuse instance:")

try:
    l = Langfuse(public_key="pk", secret_key="sk")
    print("\nSignature of start_span:")
    print(inspect.signature(l.start_span))
except Exception as e:
    print(e)
