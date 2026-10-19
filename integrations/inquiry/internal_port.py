"""RR60: a pending TE connection creates a residual-inspection obligation.

The actual flower closes first. A notice is then obtained from the unchanged
RR53 ordered readout, before constructing its next context. Notices are not
cell certificates, and all source/decoder validation remains exact.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q

import inquiry_probe as probe
from inquiry_probe import d

te=d.embedded
PARENT='07fcd606f15553e4d323d8f029ef1ac7b0967dc3'


@dataclass(frozen=True)
class Flight:
    first: te.FirstClosure
    pair: d.RetainedPair
    local_certificate: d.ReplacementCertificate

    @property
    def digest(self):
        r=self.first.receipt
        return d.fingerprint((PARENT,r.prepared.state.mode,r.prepared.spec.gain,
            r.contact_index,r.petal_choice,self.pair.digest,self.first.actual_endpoint,
            self.first.fixed_result,self.first.tolerance,self.first.residue.internal_context,
            tuple(leaf.weights for leaf in self.first.residue.terminal_operation.leaves()),
            self.first.closed_engine.lower.live.accumulated,
            self.first.closed_engine.upper.live.accumulated,
            len(self.first.closed_engine.stock),len(self.first.closed_engine.events)))


def begin(mode='keep',contact=1,petal=0,gain=Q(1)):
    # Completed 3+1 snapshots are authenticated inputs. No new neural training
    # or future-frame construction is used to obtain this first closure.
    prepared=te.prepare(mode,gain)
    first=te.execute_first(te.FirstReceipt(prepared,contact,petal))
    c=prepared.candidates[contact]
    pair=d.RetainedPair(c.leaf,prepared.candidates[0].leaf,c.shift,prepared.receiver.delta,
        f'{PARENT}:RR60:{mode}:{gain}:{contact}:{petal}')
    scope=d.Scope((first.residue.internal_context,),entry='RR60-first-current-kernel')
    certificate=d.assess(pair,scope)
    if certificate.status!=d.SAFE:raise ValueError('the declared local readout must remain equivalent')
    return Flight(first,pair,certificate)


def verify_flight(flight):
    if type(flight) is not Flight:raise ValueError('a completed authenticated first flight is required')
    r=flight.first.receipt
    if flight!=begin(r.prepared.state.mode,r.contact_index,r.petal_choice,r.prepared.spec.gain):
        raise ValueError('the first receipt, actual closure or retained source was changed')
    return True


def leaf_view(flight):
    """Source positions are occurrences of the source operator, not value IDs."""
    first=flight.first;source=first.residue.source
    head=first.closed_engine.designated_head
    if source==head or source.leaves()!=(flight.pair.original,):
        raise ValueError('one distinct primitive source and the original head are required')
    leaves=[];positions=[]
    for op in first.residue.terminal_operation.cell.beta:
        if op==source:
            positions.append(len(leaves)+1);leaves.extend(source.leaves())
        elif op==head:leaves.extend(head.leaves())
        else:raise ValueError('the declared executed word contains only its head and source')
    if not positions:raise ValueError('the source must actually occur in the closed word')
    denominator=Q(len(leaves)*(len(leaves)+1),2)
    return tuple(leaves),tuple(positions),sum(positions)/denominator


def direction_tensor(pair):
    library=pair.original.library
    return tuple(tuple(sum(weight*op.source.endpoint[i][j] for weight,op in zip(pair.direction,library))
                       for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class PortNotice:
    flight_digest: str
    strength: Q
    source_mass: Q
    direction: tuple
    requested: bool
    observation: str='next-context'

    @property
    def digest(self):
        return d.fingerprint((self.flight_digest,self.strength,self.source_mass,
                              self.direction,self.requested,self.observation))


def notice(flight,spec):
    """Does the required next-context readout depend on the retained difference?

    Delta Y = strength * source_mass * shift * direction_tensor.
    Only the zero/nonzero factors are tested. No next context, target, exact
    retained response, original tensor or next-source plan is calculated here.
    Entry authentication and actual first-cell certification are separate.
    """
    if type(flight) is not Flight or type(spec) is not te.pair.ConnectionSpec or spec.mode!='anchored':
        raise ValueError('a completed flight and the declared anchored connection are required')
    _,_,mass=leaf_view(flight)
    direction=direction_tensor(flight.pair)
    requested=bool(spec.strength and mass and flight.pair.shift and any(x for row in direction for x in row))
    return PortNotice(flight.digest,spec.strength,mass,direction,requested)


def verify_notice(flight,spec,signal):
    if type(signal) is not PortNotice or signal!=notice(flight,spec):
        raise ValueError('the retained source, actual order, port or notice evidence changed')
    return True


def reference_context(flight,spec):
    """Counterfactual readout, never an edit or a newly certified operation."""
    leaves,positions,_=leaf_view(flight)
    den=Q(len(leaves)*(len(leaves)+1),2)
    library=flight.pair.original.library
    raw=tuple(tuple(sum(Q(k)/den*sum(w*op.source.endpoint[i][j]
        for w,op in zip((flight.pair.representative if k in positions else leaf).weights,library))
        for k,leaf in enumerate(leaves,1)) for j in range(3)) for i in range(3))
    anchor=te.pair.boundary_readout(flight.first.closed_engine.designated_head)
    y=te.port.single.context(tuple(tuple(anchor[i][j]+spec.strength*(raw[i][j]-(Q(1,3) if i==j else 0))
                                      for j in range(3)) for i in range(3)))
    return raw,y


@dataclass(frozen=True)
class ConnectionRequest:
    flight: Flight
    spec: te.pair.ConnectionSpec
    waiting: object
    notice: PortNotice


def request_connection(flight,spec=te.pair.ConnectionSpec()):
    """Current elects to connect; the required readout creates its own notice.

    A completed flower may also stop. This function is called only when the
    current continuation request is made; it does not force another flower.
    """
    verify_flight(flight)
    waiting=te.request_boundary(flight.first.closed_engine)
    signal=notice(flight,spec)
    return ConnectionRequest(flight,spec,waiting,signal)


@dataclass(frozen=True)
class Delivery:
    request: ConnectionRequest
    raw_port: tuple
    context: tuple
    arrived: object
    exposure: probe.InspectionSignal

    @property
    def flight(self):return self.request.flight
    @property
    def spec(self):return self.request.spec
    @property
    def notice(self):return self.request.notice


def emit(request):
    # An advisory notice never authorizes production. Recheck the entire
    # completed first occurrence against its canonical trusted input here.
    if type(request) is not ConnectionRequest:raise ValueError('the bound current connection request is required')
    flight,spec,signal=request.flight,request.spec,request.notice
    verify_flight(flight);verify_notice(flight,spec,signal)
    if request.waiting!=te.request_boundary(flight.first.closed_engine):
        raise ValueError('the original current request or its inherited state changed')
    raw,y=te.pair.connection_context(flight.first,spec)
    emitted=te.port.event(request.waiting,'rr53-terminal-residue-port-emitted')
    arrived=te.accept_context(emitted,y)
    scope=d.Scope((y,),entry='RR60-internally-arrived-kernel')
    exposure=probe.initiate(flight.pair,scope)
    return Delivery(request,raw,y,arrived,exposure)


def verify_delivery(delivery):
    if type(delivery) is not Delivery or delivery!=emit(delivery.request):
        raise ValueError('the original internally generated context or inheritance changed')
    return True


def continue_one(delivery,branch=0,petal=0):
    """After notice/delivery only, use existing source planning and closure."""
    verify_delivery(delivery)
    if delivery.spec!=te.pair.ConnectionSpec():
        raise ValueError('this continuation replay uses the unchanged default RR53 connection')
    if branch not in (0,1) or petal not in (0,1):raise ValueError('one declared source and word branch are required')
    plan=te.resolve_open(delivery.arrived)
    if plan.phase!='PLANNED':raise ValueError('a new source plan is required in this finite example')
    cfg=te.pair.Configuration(source_branch='first' if branch==0 else 'second',petal_choice=petal)
    anchor=te.pair.EntryAnchor(cfg,delivery.flight.first.closed_engine,delivery.context,plan)
    certificate=te.triple.source_witness(anchor,branch)
    ready=te.pair.ready_second(anchor,certificate)
    pool=te.port.single.candidates(ready.problem,4)
    if len(pool)!=2:raise ValueError('the unchanged local two-word family is required')
    machine=te.triple.commit_from_pool(ready,pool);receipt=machine.commitment
    while machine.cursor<len(receipt.word):machine=te.pair.advance(machine,receipt)
    record=te.pair.close(machine,receipt).record
    if te.triple.replay_frozen(record,delivery.flight.first)!=record:
        raise ValueError('the continuation must inherit the actual first flight')
    return record,certificate


def cancellation_control(flight,spec):
    """A primitive source-line control; not a new authenticated neural contact.

    For diagonal frames the response factor is a scalar affine function of
    shift. Solve its nonzero cancellation exactly, without claiming a new
    completed operation. This tests the limit of the pointwise exposure rule.
    """
    if not spec.strength:raise ValueError('positive connection strength is required')
    _,y0=reference_context(flight,spec)
    direction=direction_tensor(flight.pair)
    _,_,mass=leaf_view(flight)
    intercept=tuple(d.join(direction,y0))
    slope=tuple(spec.strength*mass*x for x in d.join(direction,direction))
    if any(intercept[1:]) or any(slope[1:]) or not slope[0]:
        raise ValueError('this control is restricted to the declared diagonal scalar class')
    shift=-intercept[0]/slope[0]
    y=te.port.single.context(tuple(tuple(y0[i][j]+spec.strength*mass*shift*direction[i][j]
                                       for j in range(3)) for i in range(3)))
    leaf=d.AffineLetter(tuple(w+shift*v for w,v in zip(flight.pair.representative.weights,
        flight.pair.direction)),flight.pair.original.library)
    pair=d.RetainedPair(leaf,flight.pair.representative,shift,flight.pair.direction,
        'RR60-declared-source-line-cancellation-control')
    return pair,y,y0
