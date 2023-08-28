import psycopg
from azure.identity import ManagedIdentityCredential
from psycopg_pool import ConnectionPool
import threading
import random

# Replace with your PostgreSQL Flexible Server details
server_name = "dbm-postgres13-flex-server.postgres.database.azure.com"
database_name = "dbmorders"
client_id = "c8d2cd7d-3e43-46cb-9bd9-050706399f52"
username = "dbm-datadog-test-identity"
database_names = ["dbmorders", "postgres", "dbmorders_1"]

DEFAULT_PERMISSION_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

try:
    def generate_managed_identity_token(client_id: str, identity_scope: str = None):
        credential = ManagedIdentityCredential(client_id=client_id)
        if not identity_scope:
            identity_scope = DEFAULT_PERMISSION_SCOPE
        return credential.get_token(identity_scope).token

    def get_conn_pool(dbname="postgres"):
        args = {"autocommit": True, "cursor_factory": psycopg.ClientCursor}
        password = generate_managed_identity_token(client_id=client_id, identity_scope=DEFAULT_PERMISSION_SCOPE)
        print(password)
        conn_args = {
            'host': server_name,
            'user': username,
            'password': password,
            'dbname': dbname,
            'sslmode': "require"
        }
        args.update(conn_args)
        return ConnectionPool(min_size=1, kwargs=args, open=True, name=dbname)

    def run_thread(dbname):
        with get_conn_pool(dbname).connection() as tconn:
            with tconn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print("PostgreSQL version:", version)

    threads = []
    for _ in range(10):
        dbname = random.choice(database_names)
        thread = threading.Thread(target=run_thread,args=(dbname,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


except Exception as e:
    print("Error:", e)
