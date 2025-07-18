import sqlite3
import uuid

class ComputerDatabase:
    def __init__(self, db_name='computers.db'):
        # Connect to SQLite database (or create it if it doesn't exist)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
        # Create a table to store computer records
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS computers (
            uuid TEXT PRIMARY KEY,
            pid INT,
            user TEXT,
            local_ip TEXT NOT NULL
        )
        ''')
        self.conn.commit()

    def insert_computer(self, pid, user, local_ip):
        # Generate a UUID
        computer_uuid = str(uuid.uuid4())
        
        # Insert the computer record into the table
        self.cursor.execute('''
        INSERT INTO computers (uuid, pid, user, local_ip) VALUES (?, ?, ?, ?)
        ''', (computer_uuid, pid, user, local_ip))
        
        # Commit the changes
        self.conn.commit()
        return computer_uuid

    def get_computers(self):
        # Query the database to retrieve all computer records
        self.cursor.execute('SELECT * FROM computers')
        rows = self.cursor.fetchall()
        return rows

    def close(self):
        # Close the database connection
        self.conn.close()

# Example usage
#if __name__ == "__main__":
#    db = ComputerDatabase()

#    # Insert a new computer record
#    #computer_uuid = db.insert_computer(pid=1234, user='John Doe', local_ip='192.168.1.10')
#    print(f'Inserted computer with UUID: {computer_uuid}')

#    # Retrieve and print all computer records
#    computers = db.get_computers()
#    for computer in computers:
#        print(computer)

#    # Close the database connection
#    db.close()

