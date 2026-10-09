"""The durable simulated gateway (S2-01b).

A separate process on the public side of the truth barrier. It receives public
device reports and a frozen registered acquisition snapshot from the Lab host,
allocates durable SourceEnvelope V3 identity in a SQLite ledger, and seals
homogeneous IngestionBatch V2 bytes. It imports `assetops_contracts` only.
"""
