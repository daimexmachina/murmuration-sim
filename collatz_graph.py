#!/usr/bin/env python3
"""Directed graph of the Collatz map f(n) = n/2 (even) | 3n+1 (odd).

Edges point n -> f(n). Every node has out-degree 1; the graph is a single
tree rooted at 1 (the only node with out-degree 0). We build the tree by
walking the *reverse* map (predecessors) so the layout is a clean hierarchy
rooted at 1.
"""
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 40          # include all numbers 1..N in the tree
MAX_DEPTH = 12  # cap depth so the figure stays readable

def predecessors(n):
    """All positive integers m with f(m) = n."""
    out = []
    if (n - 1) % 3 == 0 and ((n - 1) // 3) % 2 == 1 and (n - 1) // 3 > 0:
        out.append((n - 1) // 3)   # odd m: 3m+1 = n
    out.append(2 * n)              # even m: m/2 = n
    return out

G = nx.DiGraph()
G.add_node(1)
frontier = [1]
depth = {1: 0}
while frontier:
    n = frontier.pop(0)
    if depth[n] >= MAX_DEPTH:
        continue
    for p in predecessors(n):
        if p <= N and p not in G:
            G.add_edge(p, n)   # p -> n  (p maps to n under f)
            depth[p] = depth[n] + 1
            frontier.append(p)

print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
print("Out-degree of every node is 1 (except root 1):",
      all(G.out_degree(n) == 1 for n in G if n != 1))

# --- layout: hierarchical, root 1 at top, children below ---
pos = {}
def place(n, x, y, dx):
    pos[n] = (x, y)
    kids = [c for c in G.predecessors(n)]  # predecessors = children (p -> n)
    if not kids:
        return
    w = dx / len(kids)
    for i, k in enumerate(kids):
        place(k, x - dx/2 + w*(i + 0.5), y - 1.0, w * 0.9)

place(1, 0, 0, 1.0)

fig, ax = plt.subplots(figsize=(16, 10))
nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowstyle="-|>",
                       arrowsize=14, edge_color="#8a8f98", width=1.1,
                       connectionstyle="arc3,rad=0.0")
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=520, node_color="#3b82f6",
                       edgecolors="#1e3a8a", linewidths=1.2)
nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_color="white",
                        font_weight="bold")
ax.set_title("Collatz map  f(n) = n/2 (even) | 3n+1 (odd)   —   directed graph, "
             f"numbers 1..{N}, depth ≤ {MAX_DEPTH}",
             fontsize=13, pad=14)
ax.axis("off")
plt.tight_layout()
plt.savefig("collatz_graph.png", dpi=150, bbox_inches="tight")
print("Saved collatz_graph.png")
