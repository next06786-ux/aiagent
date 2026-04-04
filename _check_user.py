from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'lifeswarm123'))
uid = '2c2139f7-bab4-483d-9882-ae83ce8734cd'
with d.session() as s:
    # node labels and types
    r = s.run('MATCH (n) WHERE n.user_id = $uid RETURN labels(n) AS lbl, n.type AS typ, n.entity_type AS etype, n.category AS cat, n.name AS name LIMIT 20', uid=uid)
    for row in r:
        print(row['lbl'], '| type:', row['typ'], '| entity_type:', row['etype'], '| category:', row['cat'], '| name:', row['name'])
d.close()
