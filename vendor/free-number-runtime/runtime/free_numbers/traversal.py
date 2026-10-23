"""Iterative postorder traversal; expression depth is not Python stack depth."""


def postorder(roots, children, max_nodes=None):
    seen = set()
    for root in roots:
        stack = [(root,False)]
        while stack:
            node,leaving = stack.pop()
            if leaving:
                yield node
                continue
            if node.digest in seen:
                continue
            seen.add(node.digest)
            if max_nodes is not None and len(seen) > max_nodes:
                raise ValueError('checkpoint node budget exceeded')
            stack.append((node,True))
            stack.extend((child,False) for child in reversed(children(node)))
