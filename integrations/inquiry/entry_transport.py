"""E1: receive an authenticated, fixed RR69 entry without its generators.

The first profile admits the existing diagonal source family, contacts 1/2,
petal 0, gain 1, against the pinned RR56 upstream inputs. Verification replays
frozen exact TE history; it never trains the source or selects another past.
"""
from dataclasses import replace
from fractions import Fraction as Q
import json,hashlib,re
import synthesized_resolution as a
import adaptive_resolution as adaptive
import incremental_resolution as incremental
import synthesized_session as session
import live_checkpoint as checkpoint
from synthesized_resolution import m,fn,b,prior

SCHEMA='time-engine-portable-entry-e1-v1'
MODEL='rr69-diagonal-two-origin-entry-v1'
MAX_BYTES=2_000_000
MAX_NODES=4096


def _flight(flight,contact):
    previous=prior.previous;te=previous.te;d=previous.d
    if type(flight) is not previous.Flight:raise ValueError('complete original flight required')
    first=flight.first;r=first.receipt;p=r.prepared;mode=p.state.mode
    if mode not in ('keep','erase','restore') or r.contact_index!=contact or r.petal_choice!=0 or p.spec!=te.port.PortSpec(gain=Q(1)):
        raise ValueError('unsupported fixed entry profile')
    # published_record uses the existing trusted-hash transport path. No
    # prepare/begin/register generator, source training or root search is used.
    frozen=te.published_record('erase-primary' if mode=='erase' else 'keep-primary').commitment
    state=replace(frozen.state,mode=mode);spec=te.port.PortSpec(gain=Q(1))
    prepared=te.port.Prepared(state,frozen.receiver,spec,
        tuple(te.port.contact_candidate(state,frozen.receiver,spec,i) for i in range(4)))
    if p!=prepared or te.execute_first(r)!=first:raise ValueError('frozen source or actual first history changed')
    c=prepared.candidates[contact]
    pair=d.RetainedPair(c.leaf,prepared.candidates[0].leaf,c.shift,prepared.receiver.delta,
        f'{previous.PARENT}:RR60:{mode}:1:{contact}:0')
    certificate=d.assess(pair,d.Scope((first.residue.internal_context,),entry='RR60-first-current-kernel'))
    if flight.pair!=pair or flight.local_certificate!=certificate or certificate.status!=d.SAFE:
        raise ValueError('source relation or local equivalence changed')
    y=first.residue.internal_context
    geometry=prior.geom.certify_pair(y,pair.original,pair.representative)
    head=first.closed_engine.designated_head;axis=geometry.coefficient_axis;library=pair.original.library
    if (first.actual_endpoint!=b.NEG or first.closed_engine.upper.live.accumulated!=b.NEG
        or prior.scalar(head.kernel(y))!=Q(-1,9) or prior.scalar(pair.original.kernel(y))!=-9
        or any(sum(c*op.apply(y)[j] for c,op in zip(axis,library)) for j in range(4))):
        raise ValueError('the actual current chart or inherited endpoint changed')
    return head,geometry,axis,library


def _assemble(roots):
    if type(roots) is not tuple or len(roots)!=4:raise ValueError('four complete physical entry roots required')
    first_flight,second_flight,engine,u_operation=roots
    head,geometry,axis,library=_flight(first_flight,1)
    _,second_geometry,direction,second_library=_flight(second_flight,2)
    if second_library!=library or second_flight.pair.representative!=first_flight.pair.representative:
        raise ValueError('the two original sources must share one chart')
    if first_flight.first.residue.source not in first_flight.first.closed_engine.stock:
        raise ValueError('retained S must be published in the original stock')
    base_matrix=m.d.tensor(first_flight.pair.representative)
    axis_matrix=tuple(tuple(sum(z*op.source.endpoint[i][j] for z,op in zip(axis,library)) for j in range(3)) for i in range(3))
    if any(base_matrix[i][j] or axis_matrix[i][j] for i in range(3) for j in range(3) if i!=j):raise ValueError('diagonal source chart required')
    if tuple(x.weights for x in head.leaves())!=((Q(1),0,0,0,0,0),(0,Q(1),0,0,0,0)):
        raise ValueError('the inherited head changed')
    envelope=(Q(-1,1024),Q(1,1024));base=fn.matrix_block(base_matrix);delta=fn.matrix_block(axis_matrix)
    first_vault=fn.Vault()
    first_source=fn.retained(first_vault,'retained-s',geometry.shift,envelope,first_flight.digest,base,delta)
    first=b.Entry(first_flight,first_vault,first_source,base,delta,head,axis,library,envelope)
    U_leaf=m.d.AffineLetter(tuple(x+second_geometry.shift*z for x,z in zip(second_flight.pair.representative.weights,direction)),library)
    ready,u=m.plant.produce(first_flight.first.closed_engine,first_flight.first.residue.internal_context,U_leaf,'rr65-prior-U-planned')
    bootstrap=m.plant.consume(ready,(ready.pending.head,u),'rr65-prior-U')
    if u!=u_operation or bootstrap.engine!=engine:raise ValueError('actual U publication, inheritance or bootstrap history changed')
    if tuple(x+geometry.shift*z for x,z in zip(first_flight.pair.representative.weights,axis))!=first_flight.pair.original.weights:
        raise ValueError('retained S coefficients changed')
    vault=fn.Vault();S=fn.retained(vault,'s',geometry.shift,envelope,first.digest,base,delta)
    direction_matrix=tuple(tuple(sum(z*op.source.endpoint[i][j] for z,op in zip(direction,library)) for j in range(3)) for i in range(3))
    U=fn.retained(vault,'t',second_geometry.shift,envelope,second_flight.digest,base,fn.matrix_block(direction_matrix))
    joint=vault.register('p',geometry.shift*second_geometry.shift,(Q(-1,1024**2),Q(1,1024**2)),
        a.fingerprint(('registered-product',S.digest,U.digest)))
    digest=a.fingerprint((first.digest,second_flight.digest,'diagonal',S.digest,U.digest,joint.digest,u.visible,len(engine.events)))
    mixed=m.Entry(first,second_flight,'diagonal',vault,S,U,u_operation,engine,direction,digest)
    derived=fn.Vault();s,t=geometry.shift,second_geometry.shift;eps=Q(1,1024)
    derived.register('sum',s+t,(-2*eps,2*eps),a.fingerprint((mixed.digest,'sum','s','t')))
    for word in m.WORDS:
        aa,bb=adaptive.port_weights(mixed,word)
        derived.register('port-'+word,aa*s+bb*t,(-(aa+bb)*eps,(aa+bb)*eps),a.fingerprint((mixed.digest,'RR53-primitive-position',word,aa,bb)))
    old=adaptive.Entry(mixed,derived,a.fingerprint((mixed.digest,tuple(ref.digest for ref,value in derived._records()))))
    heads=tuple(m.d.tensor(x) for x in head.leaves())
    axes=(axis_matrix,direction_matrix)
    matrices=(base_matrix,*axes,*heads)
    if any(x[i][j] for x in matrices for i in range(3) for j in range(3) if i!=j):raise ValueError('diagonal incremental basis required')
    basis=tuple(tuple(x[i][i] for i in range(3)) for x in matrices)
    if sum(basis[0])!=1 or any(sum(x) for x in basis[1:3]) or any(sum(x)!=1 for x in basis[3:]):raise ValueError('basis trace changed')
    core=incremental.Entry(old,basis,a.fingerprint((incremental.SCHEMA,old.digest,basis)))
    result=a.Entry(core,fn.Vault(),a.fingerprint((a.SCHEMA,core.digest)))
    return result,(mixed,old,core,result)


def dumps(entry):
    a.verify_entry(entry)
    if entry.derived._records():raise ValueError('entry export requires the stage before numeric observation acquisition')
    e=entry.base
    roots=(e.first.flight,e.second,e.engine,e.U_operation)
    # Export checks the same profile and actual histories as import, so an
    # issued but unsupported profile cannot produce an unreadable archive.
    candidate,_=_assemble(roots)
    if candidate.digest!=entry.digest or session.archives(candidate)!=session.archives(entry):raise ValueError('entry and complete original number state disagree')
    graph=checkpoint.pack(roots)
    if len(graph['nodes'])>MAX_NODES:raise ValueError('entry node budget exceeded')
    doc=dict(schema=SCHEMA,model=MODEL,entry_digest=entry.digest,graph=graph,numbers=session.archives(entry))
    raw=(json.dumps(doc,separators=(',',':'))+'\n').encode()
    if len(raw)>MAX_BYTES:raise ValueError('entry byte budget exceeded')
    return raw,hashlib.sha256(raw).hexdigest()


def loads(raw,trusted_sha256,expected_entry_digest):
    if (type(raw) is not bytes or len(raw)>MAX_BYTES or type(trusted_sha256) is not str
        or re.fullmatch('[0-9a-f]{64}',trusted_sha256) is None or hashlib.sha256(raw).hexdigest()!=trusted_sha256
        or type(expected_entry_digest) is not str or re.fullmatch('[0-9a-f]{64}',expected_entry_digest) is None):
        raise ValueError('bounded original bytes, external trusted hash and expected entry required')
    doc=json.loads(raw)
    if (type(doc) is not dict or set(doc)!={'schema','model','entry_digest','graph','numbers'} or doc['schema']!=SCHEMA
        or doc['model']!=MODEL or doc['entry_digest']!=expected_entry_digest):raise ValueError('original fixed entry profile required')
    graph=doc['graph']
    if type(graph) is not dict or set(graph)!={'root','nodes'} or type(graph['nodes']) is not list or len(graph['nodes'])>MAX_NODES:
        raise ValueError('bounded known-type entry graph required')
    roots=checkpoint.unpack(graph)
    if checkpoint.pack(roots)!=graph:raise ValueError('canonical complete graph required; no unused or substituted nodes')
    entry,issued=_assemble(roots)
    if entry.digest!=expected_entry_digest or session.archives(entry)!=doc['numbers']:
        raise ValueError('expected entry or complete exact number state changed')
    # Authority is issued only after provenance, exact physical replay, fibre
    # relations, archived numbers and the caller's original identity all pass.
    for registry,obj in zip((m._ISSUED,adaptive._ISSUED,incremental._ISSUED,a._ISSUED),issued):registry.append(obj)
    a.verify_entry(entry)
    return entry
