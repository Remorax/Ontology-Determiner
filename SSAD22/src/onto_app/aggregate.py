from sqlalchemy import create_engine

import subprocess, os
from rdflib.namespace import OWL, RDF, RDFS

RESTRICTIONS = "Restriction_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"
CLASSES = "Class_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"
SUBCLASSES = "Subclass_removal-1.0-SNAPSHOT-jar-with-dependencies.jar"

def accepted(decisions):
    count_accept = 0
    count_reject = 0
    for d in decisions:
        if d == 0:
            count_reject += 1
        else:
            count_accept += 1
    return bool(count_accept >= count_reject)

def generate_final_ontology(name):
    engine = create_engine('sqlite:///onto.db', echo = True)
    # conn = sqlite3.connect('onto.db')
    # c = conn.cursor()
    c = engine.connect()
    trans = c.begin()
    try:
        result = c.execute('''SELECT id FROM ontologies WHERE name = ?''', (name,))
        onto_id = None
        res = result.fetchone()
        if res:
            onto_id = res[0]
        else:
            raise ValueError
        # print (onto_id, RDFS.subClassOf)
        owl_path = './data/final/' + name + '.owl'
        if not os.path.isfile(owl_path):
            try:
                subprocess.run(['cp', './data/owl/' + name + '.owl', owl_path])
            except:
                raise RuntimeError

        result = c.execute("""SELECT * FROM class_relations WHERE onto_id = ?""", (onto_id,))
        relations = result.fetchall()
        # print ("**",relations, "**")
        for r in relations:
            # print (r)
            result = c.execute("""SELECT * FROM class_decisions WHERE relation_id = ?""", (r[0],))
            decisions = result.fetchall()
            if decisions:
                print (type(decisions), type(decisions[0]))
                if not accepted([d['approved'] for d in decisions]):
                    print(type(r['quantifier']))
                    print(type(RDFS.subClassOf))
                    if r['quantifier'] == str(RDFS.subClassOf):
                        try:
                            subprocess.run(['java', '-jar', SUBCLASSES, r['domain'], r['range'], owl_path])
                        except:
                            raise RuntimeError
                    else:
                        try:
                            subprocess.run(['java', '-jar', RESTRICTIONS, r['domain'], r['property'], r['range'], owl_path])
                        except:
                            raise RuntimeError
                c.execute("""DELETE FROM class_relations WHERE id = ?""", r['id'])
        
        result = c.execute("""SELECT * FROM nodes WHERE onto_id = ?""", (onto_id,))
        nodes = result.fetchall()
        print (nodes)
        for n in nodes:
            print (n)
            result = c.execute("""SELECT * FROM node_decisions WHERE node_id = ?""", n['id'])
            decisions = result.fetchall()
            if decisions:
                if not accepted([d['approved'] for d in decisions]):
                    try:
                        subprocess.run(['java', '-jar', CLASSES, n['name'], owl_path])
                    except:
                        raise RuntimeError
                c.execute("""DELETE FROM nodes WHERE id = ?""", n['id'])
        
        trans.commit()
    except:
        trans.rollback()
        raise
    
    