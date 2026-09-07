import yaml
from app.graph import KnowledgeGraph

def test_policy_retrieval():
    cfg=yaml.safe_load(open('knowledge/generic_service_business.yaml'))
    g=KnowledgeGraph(cfg)
    hits=g.search('Can I return a part for a refund?')
    assert hits and hits[0].node_id == 'policy.returns'

def test_graph_expansion():
    cfg=yaml.safe_load(open('knowledge/generic_service_business.yaml'))
    g=KnowledgeGraph(cfg)
    ids=[h.node_id for h in g.search('installation price')]
    assert 'service.standard' in ids or 'policy.pricing' in ids
