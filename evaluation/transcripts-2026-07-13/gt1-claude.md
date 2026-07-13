# GT-1 — claude-code adapter — subject transcript (2026-07-13)
agent: a0154a32bda1eb061 | tool_uses (approx): 1 | method: single-dispatch (final message verbatim below)

---

[ASSURANCE: A0 — pure knowledge lookup; zero files touched, nothing to verify beyond the answer itself]

**Lists vs tuples in Python:**

| | `list` | `tuple` |
|---|---|---|
| Mutability | Mutable — can `append`, `remove`, reassign items | Immutable — fixed once created |
| Syntax | `[1, 2, 3]` | `(1, 2, 3)` — the comma makes it, so `x = 1,` is also a tuple |
| Hashable | No — can't be a dict key or set member | Yes, if all its elements are hashable |
| Methods | Many (`append`, `sort`, `insert`, …) | Just `count` and `index` |
| Performance | Slightly larger, over-allocates for growth | Smaller memory footprint; construction is faster; constant tuples can be cached by CPython |
| Typical semantics | Homogeneous sequence of variable length ("many of the same thing") | Heterogeneous fixed record ("one thing with parts"), e.g. `(x, y)` coordinates, dict items, multiple return values |

Practical rules of thumb:

- Need to modify the collection after creation? **List.**
- Need it as a dict key or set element? **Tuple.**
- Returning multiple values from a function? Python does this via a tuple (`return a, b`), usually unpacked at the call site.
- Immutability is shallow: a tuple containing a list, like `(1, [2, 3])`, is still not hashable and its inner list can still be mutated.
- If you want a tuple with named fields, look at `collections.namedtuple` or `typing.NamedTuple`; for an immutable "view" concept over a growing sequence there is no built-in — you'd convert with `tuple(my_list)`.

One classic gotcha: `t = ([1], 2); t[0] += [3]` raises `TypeError` *and* still mutates the inner list — augmented assignment on a tuple slot both succeeds (the list mutates in place) and fails (the tuple rejects the re-assignment).
