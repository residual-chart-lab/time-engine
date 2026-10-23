"""Verbatim RR66 pre-audit derivation, for behavioral A/B measurement only.

Source commit cb4d505dd1c93bd1b6194593a1225500f0e304e4; never used by the runtime.
"""
from adaptive_resolution import m,port_weights

def derive_cached(entry,key,cache):
    values={k:record[1] for k,record in cache.items()}
    pair=None
    if 's' in values and 't' in values:pair=values['s'],values['t']
    elif 'sum' in values:
        for word in m.WORDS:
            if 'port-'+word in values:
                a,b_=port_weights(entry.base,word);z=values['port-'+word];u=values['sum']
                pair=((b_*u-z)/(b_-a),(z-a*u)/(b_-a));break
    elif all('port-'+w in values for w in m.WORDS):
        a,b_=port_weights(entry.base,m.WORDS[0]);c,d=port_weights(entry.base,m.WORDS[1])
        x,y=(values['port-'+w] for w in m.WORDS);det=a*d-b_*c
        pair=((d*x-b_*y)/det,(a*y-c*x)/det)
    if pair is None:return None
    s,t=pair
    if key=='s':return s
    if key=='t':return t
    if key=='p':return s*t
    if key=='sum':return s+t
    a,b_=port_weights(entry.base,key[len('port-'):]);return a*s+b_*t

