from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'lifeswarm123'))
with d.session() as s:
    for uid in ['2c2139f7-bab4-483d-9882-ae83ce8734cd', 'default_user']:
        r = s.run(
            'MATCH (n) WHERE n.user_id = $uid RETURN labels(n) AS lbl, count(n) AS cnt',
            uid=uid
        )
        print('---', uid, '---')
        for row in r:
            print(row['lbl'], row['cnt'])
d.close()
