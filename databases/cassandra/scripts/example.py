from cassandra.cluster import Cluster
import os

contact_points_str = os.getenv('CASSANDRA_CONTACT_POINTS')
username = os.getenv('CASSANDRA_USERNAME')
password = os.getenv('CASSANDRA_PASSWORD')

contact_points = [cp.strip() for cp in contact_points_str.split(',')]

cluster = Cluster(contact_points, auth_provider=PlainTextAuthProvider(username=username, password=password))
session = cluster.connect('your_keyspace')