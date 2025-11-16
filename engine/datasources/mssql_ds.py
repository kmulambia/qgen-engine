import pyodbc
from typing import Optional


class MSSQLDS:
    def __init__(
            self,
            server: str,
            database: str,
            username: Optional[str] = None,
            password: Optional[str] = None,
            port: Optional[int] = None,
            driver: str = "ODBC Driver 17 for SQL Server",
            ssl: bool = False
    ):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.port = port if port else 1433
        self.ssl = ssl
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish connection to MSSQL database"""
        try:
            connection_parts = [
                f"DRIVER={{{self.driver}}}",
                f"SERVER={self.server}",
                f"DATABASE={self.database}",
            ]

            if self.username and self.password:
                connection_parts.append(f"UID={self.username}")
                connection_parts.append(f"PWD={self.password}")
            
            if self.ssl:
                connection_parts.append(f"Trusted_Connection=yes;")
               
            connection_string = ";".join(connection_parts)

            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
        except pyodbc.Error as e:
            self.connection = None
            self.cursor = None
            raise Exception(f"Database connection error: {str(e)}")

    def get_cursor(self):
        """Get cursor, connecting first if necessary"""
        if self.connection is None or self.cursor is None:
            self.connect()
        return self.cursor

    def disconnect(self):
        """Close cursor and connection"""
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.cursor = None
