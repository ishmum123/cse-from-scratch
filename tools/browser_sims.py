"""Browser simulation HTML generator for each chapter."""


def base(title, body, script):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 1rem; text-align: center; }}
  canvas {{ border: 1px solid #ccc; display: block; margin: 1rem auto; background: #fafafa; }}
  .controls {{ display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin: 1rem 0; }}
  button, input {{ padding: 0.5rem 0.75rem; font-size: 1rem; }}
  #status {{ min-height: 1.5rem; color: #444; }}
</style>
</head>
<body>
<h1>{title}</h1>
{body}
<script>
{script}
</script>
</body>
</html>
"""


def counting():
    return base(
        "Why Counting Exists",
        '<p>Click the stones to count them. Each click assigns the next stable symbol.</p>'
        '<div class="controls"><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Count: 0</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let count = 0;
const stones = Array.from({length: 12}, (_, i) => ({x: 40 + (i % 6) * 90, y: 60 + Math.floor(i / 6) * 70, counted: false}));
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  stones.forEach((s, i) => {
    ctx.beginPath();
    ctx.ellipse(s.x, s.y, 25, 18, 0, 0, Math.PI * 2);
    ctx.fillStyle = s.counted ? '#66bb6a' : '#bdbdbd';
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(s.counted ? i + 1 : '?', s.x, s.y + 5);
  });
}
canvas.addEventListener('click', e => {
  const r = canvas.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  stones.forEach((s, i) => {
    if (!s.counted && Math.hypot(x - s.x, y - s.y) < 30) {
      s.counted = true;
      count++;
      document.getElementById('status').textContent = `Count: ${count}`;
    }
  });
  draw();
});
document.getElementById('reset').onclick = () => { stones.forEach(s => s.counted = false); count = 0; document.getElementById('status').textContent = 'Count: 0'; draw(); };
draw();
""",
    )


def number_memory():
    return base(
        "Why Numbers Need Memory",
        '<p>Type a number, store it, then recall it later.</p>'
        '<div class="controls"><input id="num" type="number" placeholder="Enter a number"><button id="store">Store</button><button id="recall">Recall</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Memory is empty.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let memory = null;
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeRect(200, 60, 200, 80);
  ctx.fillStyle = '#333';
  ctx.font = '18px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Memory Register', 300, 50);
  ctx.font = 'bold 32px sans-serif';
  ctx.fillText(memory !== null ? memory : '—', 300, 110);
}
document.getElementById('store').onclick = () => {
  const v = document.getElementById('num').value;
  if (v !== '') { memory = v; document.getElementById('status').textContent = `Stored: ${v}`; }
  draw();
};
document.getElementById('recall').onclick = () => {
  document.getElementById('status').textContent = memory !== null ? `Recalled: ${memory}` : 'Nothing stored yet.';
};
draw();
""",
    )


def arrays():
    return base(
        "Why Arrays Exist",
        '<p>Add numbers to the array and fetch by index.</p>'
        '<div class="controls"><input id="val" type="number" placeholder="Value"><button id="add">Append</button><button id="get">Get Index</button><input id="idx" type="number" placeholder="Index" style="width:80px"></div>'
        '<canvas id="c" width="700" height="160"></canvas>'
        '<div id="status">Array: []</div>',
        """
const arr = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  arr.forEach((v, i) => {
    ctx.fillStyle = i === hi ? '#ffcc80' : '#e3f2fd';
    ctx.fillRect(10 + i * 55, 60, 50, 50);
    ctx.strokeRect(10 + i * 55, 60, 50, 50);
    ctx.fillStyle = '#333';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(v, 35 + i * 55, 90);
    ctx.font = '12px sans-serif';
    ctx.fillText(i, 35 + i * 55, 125);
  });
}
document.getElementById('add').onclick = () => {
  const v = document.getElementById('val').value;
  if (v !== '') arr.push(v);
  document.getElementById('status').textContent = `Array: [${arr.join(', ')}]`;
  draw();
};
document.getElementById('get').onclick = () => {
  const i = parseInt(document.getElementById('idx').value);
  draw(i);
  document.getElementById('status').textContent = (i >= 0 && i < arr.length) ? `arr[${i}] = ${arr[i]}` : 'Index out of bounds.';
};
draw();
""",
    )


def memory_addresses():
    return base(
        "Why Memory Has Addresses",
        '<p>Click a cell to write a value at that address, or read it back.</p>'
        '<div class="controls"><input id="addr" type="number" placeholder="Address 0-11" min="0" max="11"><input id="val" type="text" placeholder="Value"><button id="write">Write</button><button id="read">Read</button></div>'
        '<canvas id="c" width="700" height="220"></canvas>'
        '<div id="status">Select an address.</div>',
        """
const mem = Array(12).fill('');
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  mem.forEach((v, i) => {
    const x = 20 + (i % 6) * 110, y = 40 + Math.floor(i / 6) * 80;
    ctx.fillStyle = i === hi ? '#ffcc80' : '#e8f5e9';
    ctx.fillRect(x, y, 90, 55);
    ctx.strokeRect(x, y, 90, 55);
    ctx.fillStyle = '#333';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`addr ${i}`, x + 45, y + 18);
    ctx.font = 'bold 16px sans-serif';
    ctx.fillText(v || '—', x + 45, y + 42);
  });
}
document.getElementById('write').onclick = () => {
  const a = parseInt(document.getElementById('addr').value);
  const v = document.getElementById('val').value;
  if (a >= 0 && a < 12) { mem[a] = v; document.getElementById('status').textContent = `Wrote "${v}" to address ${a}.`; }
  else document.getElementById('status').textContent = 'Invalid address.';
  draw(a);
};
document.getElementById('read').onclick = () => {
  const a = parseInt(document.getElementById('addr').value);
  draw(a);
  document.getElementById('status').textContent = (a >= 0 && a < 12) ? `Read address ${a}: ${mem[a] || '(empty)'}` : 'Invalid address.';
};
draw();
""",
    )


def copying_expensive():
    return base(
        "Why Copying Is Expensive",
        '<p>Copy blocks of data. Larger blocks take more time.</p>'
        '<div class="controls"><button id="small">Copy 1 block</button><button id="medium">Copy 10 blocks</button><button id="large">Copy 50 blocks</button></div>'
        '<canvas id="c" width="600" height="160"></canvas>'
        '<div id="status">Press a button to copy.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let blocks = [];
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  blocks.forEach((b, i) => {
    ctx.fillStyle = b.copied ? '#66bb6a' : '#90caf9';
    ctx.fillRect(10 + i * 11, 40, 9, 60);
  });
}
async function copy(n) {
  blocks = Array(n).fill(0).map(() => ({copied: false}));
  document.getElementById('status').textContent = `Copying ${n} blocks...`;
  const start = performance.now();
  for (let i = 0; i < n; i++) {
    blocks[i].copied = true;
    if (i % Math.max(1, Math.floor(n / 20)) === 0) { draw(); await new Promise(r => setTimeout(r, 10)); }
  }
  draw();
  const ms = (performance.now() - start).toFixed(1);
  document.getElementById('status').textContent = `Copied ${n} blocks in ${ms} ms.`;
}
document.getElementById('small').onclick = () => copy(1);
document.getElementById('medium').onclick = () => copy(10);
document.getElementById('large').onclick = () => copy(50);
draw();
""",
    )


def locality():
    return base(
        "Why Locality Matters",
        '<p>Compare sequential vs random memory access patterns.</p>'
        '<div class="controls"><button id="seq">Sequential access</button><button id="rand">Random access</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Sequential access is cache-friendly.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const cells = Array(50).fill(0).map((_, i) => i);
let pattern = [];
function draw(next=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  cells.forEach((_, i) => {
    ctx.fillStyle = i === next ? '#ef5350' : (pattern.includes(i) ? '#66bb6a' : '#e0e0e0');
    ctx.fillRect(10 + (i % 10) * 58, 20 + Math.floor(i / 10) * 35, 50, 25);
    ctx.fillStyle = '#333';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(i, 35 + (i % 10) * 58, 37 + Math.floor(i / 10) * 35);
  });
}
async function run(type) {
  pattern = type === 'seq' ? cells.slice() : Array.from(cells).sort(() => Math.random() - 0.5);
  let cacheHits = 0;
  for (let i = 0; i < pattern.length; i++) {
    if (type === 'seq' && i > 0 && Math.abs(pattern[i] - pattern[i-1]) <= 2) cacheHits++;
    draw(pattern[i]);
    document.getElementById('status').textContent = `${type === 'seq' ? 'Sequential' : 'Random'} access: ${i+1}/${pattern.length} (${cacheHits} cache-friendly steps)`;
    await new Promise(r => setTimeout(r, 60));
  }
}
document.getElementById('seq').onclick = () => run('seq');
document.getElementById('rand').onclick = () => run('rand');
draw();
""",
    )


def linear_search():
    return base(
        "Why Looking Is Slow",
        '<p>Search for a target value one item at a time.</p>'
        '<div class="controls"><input id="target" type="number" placeholder="Target" value="42"><button id="search">Search</button></div>'
        '<canvas id="c" width="700" height="150"></canvas>'
        '<div id="status">Enter a target and search.</div>',
        """
const arr = Array.from({length: 12}, () => Math.floor(Math.random() * 100));
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1, found=false) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  arr.forEach((v, i) => {
    ctx.fillStyle = i === hi ? (found ? '#66bb6a' : '#ffcc80') : '#e3f2fd';
    ctx.fillRect(10 + i * 57, 40, 50, 50);
    ctx.strokeRect(10 + i * 57, 40, 50, 50);
    ctx.fillStyle = '#333';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(v, 35 + i * 57, 70);
  });
}
async function search() {
  const t = parseInt(document.getElementById('target').value);
  for (let i = 0; i < arr.length; i++) {
    draw(i, arr[i] === t);
    document.getElementById('status').textContent = `Checking index ${i}...`;
    await new Promise(r => setTimeout(r, 300));
    if (arr[i] === t) { document.getElementById('status').textContent = `Found ${t} at index ${i}.`; return; }
  }
  document.getElementById('status').textContent = `${t} not found.`;
}
document.getElementById('search').onclick = search;
draw();
""",
    )


def ordering_helps():
    return base(
        "Why Ordering Helps",
        '<p>Compare searching sorted vs unsorted data.</p>'
        '<div class="controls"><button id="unsorted">Unsorted search</button><button id="sorted">Sorted search</button></div>'
        '<canvas id="c" width="700" height="150"></canvas>'
        '<div id="status">Sorted data lets you stop early once the target is passed.</div>',
        """
const unsorted = [34, 12, 67, 5, 89, 21, 44, 90, 3, 55];
const sorted = [...unsorted].sort((a,b)=>a-b);
const target = 44;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(arr, hi, done, msg) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  arr.forEach((v, i) => {
    ctx.fillStyle = i === hi ? (done ? '#66bb6a' : '#ffcc80') : '#e3f2fd';
    ctx.fillRect(10 + i * 67, 40, 60, 50);
    ctx.strokeRect(10 + i * 67, 40, 60, 50);
    ctx.fillStyle = '#333';
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(v, 40 + i * 67, 70);
  });
  document.getElementById('status').textContent = msg;
}
async function run(type) {
  const arr = type === 'sorted' ? sorted : unsorted;
  for (let i = 0; i < arr.length; i++) {
    const done = arr[i] === target;
    const past = type === 'sorted' && arr[i] > target;
    draw(arr, i, done, `Checking ${arr[i]}...`);
    await new Promise(r => setTimeout(r, 400));
    if (done) { draw(arr, i, true, `Found ${target} at index ${i}.`); return; }
    if (past) { draw(arr, i, false, `${arr[i]} > ${target}; can stop early.`); return; }
  }
  draw(arr, -1, false, `${target} not found.`);
}
document.getElementById('unsorted').onclick = () => run('unsorted');
document.getElementById('sorted').onclick = () => run('sorted');
draw(unsorted, -1, false, 'Target: 44');
""",
    )


def binary_search():
    return base(
        "Why Binary Search Exists",
        '<p>Find the target by repeatedly halving the sorted list.</p>'
        '<div class="controls"><input id="target" type="number" placeholder="Target" value="42"><button id="search">Binary Search</button></div>'
        '<canvas id="c" width="700" height="150"></canvas>'
        '<div id="status">Enter a target and watch the interval shrink.</div>',
        """
const arr = [3, 7, 12, 18, 25, 31, 36, 42, 55, 61, 72, 88];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(lo, hi, mid=-1, found=false) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  arr.forEach((v, i) => {
    ctx.fillStyle = i < lo || i > hi ? '#e0e0e0' : (i === mid ? (found ? '#66bb6a' : '#ef5350') : '#ffcc80');
    ctx.fillRect(10 + i * 57, 40, 50, 50);
    ctx.strokeRect(10 + i * 57, 40, 50, 50);
    ctx.fillStyle = '#333';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(v, 35 + i * 57, 70);
  });
}
async function search() {
  let lo = 0, hi = arr.length - 1;
  const t = parseInt(document.getElementById('target').value);
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    draw(lo, hi, mid, arr[mid] === t);
    document.getElementById('status').textContent = `lo=${lo}, mid=${mid}, hi=${hi}; arr[mid]=${arr[mid]}`;
    await new Promise(r => setTimeout(r, 700));
    if (arr[mid] === t) { document.getElementById('status').textContent = `Found ${t} at index ${mid}.`; return; }
    if (arr[mid] < t) lo = mid + 1; else hi = mid - 1;
  }
  draw(-1, -1);
  document.getElementById('status').textContent = `${t} not found.`;
}
document.getElementById('search').onclick = search;
draw(0, arr.length - 1);
""",
    )


def trees_exist():
    return base(
        "Why Trees Exist",
        '<p>Insert values into a binary search tree and watch the structure grow.</p>'
        '<div class="controls"><input id="val" type="number" placeholder="Value"><button id="insert">Insert</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="700" height="300"></canvas>'
        '<div id="status">Insert values to build a BST.</div>',
        """
class Node { constructor(v) { this.v = v; this.l = null; this.r = null; this.x = 0; this.y = 0; } }
let root = null;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function insert(v) { if (!root) { root = new Node(v); return; } let n = root; while (true) { if (v < n.v) { if (!n.l) { n.l = new Node(v); return; } n = n.l; } else { if (!n.r) { n.r = new Node(v); return; } n = n.r; } } }
function layout(n, x, y, gap) { if (!n) return; n.x = x; n.y = y; layout(n.l, x - gap, y + 50, gap / 2); layout(n.r, x + gap, y + 50, gap / 2); }
function drawNode(n) { if (!n) return; if (n.l) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(n.l.x, n.l.y); ctx.stroke(); drawNode(n.l); } if (n.r) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(n.r.x, n.r.y); ctx.stroke(); drawNode(n.r); } ctx.beginPath(); ctx.arc(n.x, n.y, 18, 0, Math.PI*2); ctx.fillStyle = '#e3f2fd'; ctx.fill(); ctx.stroke(); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.v, n.x, n.y + 5); }
function draw() { ctx.clearRect(0, 0, canvas.width, canvas.height); layout(root, canvas.width/2, 40, 160); drawNode(root); }
document.getElementById('insert').onclick = () => { const v = parseInt(document.getElementById('val').value); if (!isNaN(v)) insert(v); document.getElementById('status').textContent = `Inserted ${v}. Tree height grows with order of insertion.`; draw(); };
document.getElementById('reset').onclick = () => { root = null; document.getElementById('status').textContent = 'Tree cleared.'; draw(); };
[30, 15, 45, 7, 22, 38, 60].forEach(insert);
draw();
""",
    )


def balancing_exists():
    return base(
        "Why Balancing Exists",
        '<p>Insert sorted data and see the tree become a slow linked list.</p>'
        '<div class="controls"><button id="random">Insert random</button><button id="sorted">Insert sorted</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="700" height="300"></canvas>'
        '<div id="status">Sorted input destroys an unbalanced BST.</div>',
        """
class Node { constructor(v) { this.v = v; this.l = null; this.r = null; this.x = 0; this.y = 0; } }
let root = null;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function insert(v) { if (!root) { root = new Node(v); return; } let n = root; while (true) { if (v < n.v) { if (!n.l) { n.l = new Node(v); return; } n = n.l; } else { if (!n.r) { n.r = new Node(v); return; } n = n.r; } } }
function layout(n, x, y, gap) { if (!n) return; n.x = x; n.y = y; layout(n.l, x - gap, y + 40, gap / 2); layout(n.r, x + gap, y + 40, gap / 2); }
function drawNode(n) { if (!n) return; if (n.l) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(n.l.x, n.l.y); ctx.stroke(); drawNode(n.l); } if (n.r) { ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(n.r.x, n.r.y); ctx.stroke(); drawNode(n.r); } ctx.beginPath(); ctx.arc(n.x, n.y, 15, 0, Math.PI*2); ctx.fillStyle = '#e3f2fd'; ctx.fill(); ctx.stroke(); ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.v, n.x, n.y + 4); }
function draw() { ctx.clearRect(0, 0, canvas.width, canvas.height); layout(root, canvas.width/2, 30, 160); drawNode(root); }
document.getElementById('random').onclick = () => { root = null; const vals = Array.from({length: 15}, () => Math.floor(Math.random()*100)); vals.forEach(insert); document.getElementById('status').textContent = `Random insert: tree stays relatively bushy.`; draw(); };
document.getElementById('sorted').onclick = () => { root = null; for (let i = 1; i <= 15; i++) insert(i*2); document.getElementById('status').textContent = `Sorted insert: tree degenerates to a linked list.`; draw(); };
document.getElementById('reset').onclick = () => { root = null; draw(); };
draw();
""",
    )


def hashing_exists():
    return base(
        "Why Hashing Exists",
        '<p>Map keys to buckets with a hash function. Watch collisions occur.</p>'
        '<div class="controls"><input id="key" type="text" placeholder="Key"><button id="insert">Insert</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="700" height="260"></canvas>'
        '<div id="status">Type a key and insert it into the hash table.</div>',
        """
const buckets = Array(8).fill(0).map(() => []);
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % buckets.length; return h; }
function draw(hi=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  buckets.forEach((b, i) => {
    ctx.fillStyle = i === hi ? '#ffcc80' : '#e8f5e9';
    ctx.fillRect(20, 20 + i * 28, 80, 24);
    ctx.strokeRect(20, 20 + i * 28, 80, 24);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`bucket ${i}`, 60, 37 + i * 28);
    b.forEach((k, j) => {
      ctx.fillStyle = '#90caf9'; ctx.fillRect(110 + j * 70, 20 + i * 28, 65, 24); ctx.strokeRect(110 + j * 28, 20 + i * 28, 65, 24);
      ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(k, 142 + j * 70, 37 + i * 28);
    });
  });
}
document.getElementById('insert').onclick = () => {
  const k = document.getElementById('key').value || 'key';
  const h = hash(k);
  buckets[h].push(k);
  document.getElementById('status').textContent = `Hash("${k}") = ${h}. Collisions: ${buckets[h].length > 1 ? 'yes' : 'no'}.`;
  draw(h);
};
document.getElementById('reset').onclick = () => { buckets.forEach(b => b.length = 0); draw(); };
draw();
""",
    )


def sorting_exists():
    return base(
        "Why Sorting Exists",
        '<p>Watch bubble sort bring order to a random array.</p>'
        '<div class="controls"><button id="new">New array</button><button id="sort">Bubble sort</button></div>'
        '<canvas id="c" width="700" height="200"></canvas>'
        '<div id="status">Press sort to see comparisons and swaps.</div>',
        """
let arr = Array.from({length: 12}, () => Math.floor(Math.random() * 90) + 10);
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1, hj=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  arr.forEach((v, i) => {
    ctx.fillStyle = i === hi || i === hj ? '#ef5350' : '#90caf9';
    ctx.fillRect(20 + i * 55, 160 - v, 45, v);
    ctx.strokeRect(20 + i * 55, 160 - v, 45, v);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(v, 42 + i * 55, 180 - v);
  });
}
async function sort() {
  for (let i = 0; i < arr.length; i++) {
    for (let j = 0; j < arr.length - i - 1; j++) {
      draw(j, j+1);
      document.getElementById('status').textContent = `Comparing ${arr[j]} and ${arr[j+1]}.`;
      await new Promise(r => setTimeout(r, 300));
      if (arr[j] > arr[j+1]) { [arr[j], arr[j+1]] = [arr[j+1], arr[j]]; draw(j, j+1); document.getElementById('status').textContent = `Swapped.`; await new Promise(r => setTimeout(r, 300)); }
    }
  }
  document.getElementById('status').textContent = 'Sorted.';
  draw();
}
document.getElementById('new').onclick = () => { arr = Array.from({length: 12}, () => Math.floor(Math.random() * 90) + 10); draw(); };
document.getElementById('sort').onclick = sort;
draw();
""",
    )


def divide_conquer():
    return base(
        "Why Divide and Conquer Works",
        '<p>Visualize merge sort splitting and merging halves.</p>'
        '<div class="controls"><button id="new">New array</button><button id="sort">Merge sort</button></div>'
        '<canvas id="c" width="700" height="260"></canvas>'
        '<div id="status">Merge sort divides the array, sorts halves, and merges.</div>',
        """
let arr = Array.from({length: 16}, () => Math.floor(Math.random() * 90) + 10);
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let levels = [];
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  levels.forEach((level, li) => {
    level.forEach(seg => {
      seg.arr.forEach((v, i) => {
        const x = seg.x + i * 32;
        const y = 30 + li * 55;
        ctx.fillStyle = '#90caf9'; ctx.fillRect(x, y, 28, 25);
        ctx.strokeRect(x, y, 28, 25);
        ctx.fillStyle = '#333'; ctx.font = '11px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(v, x + 14, y + 17);
      });
    });
  });
}
function buildLevels(a, depth, x, width) {
  if (!levels[depth]) levels[depth] = [];
  levels[depth].push({arr: a, x: x});
  if (a.length <= 1) return;
  const m = Math.floor(a.length / 2);
  buildLevels(a.slice(0, m), depth + 1, x, width / 2);
  buildLevels(a.slice(m), depth + 1, x + width / 2, width / 2);
}
async function sort() {
  levels = [];
  buildLevels(arr, 0, 20, 540);
  draw();
  document.getElementById('status').textContent = 'Array split into halves recursively.';
  await new Promise(r => setTimeout(r, 1000));
  arr.sort((a,b)=>a-b);
  levels = [[{arr: arr, x: 20}]];
  draw();
  document.getElementById('status').textContent = 'Sorted halves merged back together.';
}
document.getElementById('new').onclick = () => { arr = Array.from({length: 16}, () => Math.floor(Math.random() * 90) + 10); levels = [[{arr: arr, x: 20}]]; draw(); };
document.getElementById('sort').onclick = sort;
levels = [[{arr: arr, x: 20}]]; draw();
""",
    )


def dynamic_programming():
    return base(
        "Why Dynamic Programming Exists",
        '<p>Compute Fibonacci with and without memoization.</p>'
        '<div class="controls"><input id="n" type="number" value="8" min="1" max="15" style="width:60px"><button id="naive">Naive recursion</button><button id="memo">Memoized</button></div>'
        '<canvas id="c" width="700" height="280"></canvas>'
        '<div id="status">Memoization avoids recomputing the same sub-problems.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let calls = 0;
function fib(n) { calls++; if (n <= 1) return n; return fib(n-1) + fib(n-2); }
function fibMemo(n, m={}) { calls++; if (n <= 1) return n; if (m[n]) return m[n]; m[n] = fibMemo(n-1, m) + fibMemo(n-2, m); return m[n]; }
function draw(n, mode) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'left';
  ctx.fillText(`fib(${n}) using ${mode}`, 20, 30);
  ctx.fillText(`Recursive calls: ${calls}`, 20, 60);
  ctx.fillText(`Result: ${mode === 'memo' ? fibMemo(n) : fib(n)}`, 20, 90);
}
document.getElementById('naive').onclick = () => { calls = 0; const n = parseInt(document.getElementById('n').value); draw(n, 'naive'); };
document.getElementById('memo').onclick = () => { calls = 0; const n = parseInt(document.getElementById('n').value); draw(n, 'memo'); };
""",
    )


def greedy():
    return base(
        "Why Greedy Sometimes Works",
        '<p>Make change with the largest coin first. Does it always work?</p>'
        '<div class="controls"><input id="amount" type="number" value="37" style="width:80px"><button id="greedy">Greedy change</button></div>'
        '<canvas id="c" width="600" height="180"></canvas>'
        '<div id="status">Greedy picks the largest coin that fits.</div>',
        """
const coins = [25, 10, 5, 1];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function makeChange(amount) {
  const result = [];
  let remaining = amount;
  for (const c of coins) { while (remaining >= c) { result.push(c); remaining -= c; } }
  return result;
}
function draw(amount) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const change = makeChange(amount);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'left';
  ctx.fillText(`Amount: ${amount}`, 20, 30);
  change.forEach((c, i) => {
    ctx.beginPath(); ctx.arc(40 + i * 50, 90, 20, 0, Math.PI*2); ctx.fillStyle = '#ffd54f'; ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(c, 40 + i * 50, 95);
  });
  ctx.fillText(`Coins used: ${change.length}`, 20, 150);
}
document.getElementById('greedy').onclick = () => draw(parseInt(document.getElementById('amount').value));
draw(37);
""",
    )


def graphs():
    return base(
        "Why Graphs Matter",
        '<p>Run BFS from a start node to see reachable neighbors.</p>'
        '<div class="controls"><button id="bfs">Run BFS</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="300"></canvas>'
        '<div id="status">Graphs model relationships as nodes and edges.</div>',
        """
const nodes = [{id:0,x:100,y:150},{id:1,x:250,y:80},{id:2,x:250,y:220},{id:3,x:400,y:80},{id:4,x:400,y:220},{id:5,x:500,y:150}];
const edges = [[0,1],[0,2],[1,3],[2,4],[3,5],[4,5]];
let visited = new Set();
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  edges.forEach(([a,b]) => { ctx.beginPath(); ctx.moveTo(nodes[a].x, nodes[a].y); ctx.lineTo(nodes[b].x, nodes[b].y); ctx.stroke(); });
  nodes.forEach(n => { ctx.beginPath(); ctx.arc(n.x, n.y, 22, 0, Math.PI*2); ctx.fillStyle = visited.has(n.id) ? '#66bb6a' : '#e3f2fd'; ctx.fill(); ctx.stroke(); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.id, n.x, n.y + 5); });
}
async function bfs() {
  visited = new Set([0]);
  const q = [0];
  while (q.length) {
    const u = q.shift();
    draw();
    document.getElementById('status').textContent = `Visiting node ${u}.`;
    await new Promise(r => setTimeout(r, 500));
    edges.filter(([a]) => a === u).forEach(([_, v]) => { if (!visited.has(v)) { visited.add(v); q.push(v); } });
  }
  document.getElementById('status').textContent = 'BFS complete. All reachable nodes visited.';
}
document.getElementById('bfs').onclick = bfs;
document.getElementById('reset').onclick = () => { visited = new Set(); draw(); };
draw();
""",
    )


def functions():
    return base(
        "Why Functions Exist",
        '<p>Map inputs through a reusable function box.</p>'
        '<div class="controls"><input id="x" type="number" value="5" style="width:80px"><button id="run">f(x) = x² + 1</button></div>'
        '<canvas id="c" width="600" height="180"></canvas>'
        '<div id="status">A function packages a reusable transformation.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function f(x) { return x*x + 1; }
function draw(x, y) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '18px sans-serif'; ctx.textAlign = 'center';
  ctx.fillText(`x = ${x}`, 100, 80);
  ctx.fillStyle = '#e3f2fd'; ctx.fillRect(220, 40, 120, 80); ctx.strokeRect(220, 40, 120, 80);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.fillText('f(x)', 280, 85);
  ctx.beginPath(); ctx.moveTo(120, 80); ctx.lineTo(220, 80); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(340, 80); ctx.lineTo(440, 80); ctx.stroke();
  ctx.font = '18px sans-serif'; ctx.fillText(`f(x) = ${y}`, 500, 80);
}
document.getElementById('run').onclick = () => { const x = parseInt(document.getElementById('x').value); draw(x, f(x)); };
draw(5, f(5));
""",
    )


def recursion():
    return base(
        "Why Recursion Exists",
        '<p>Draw a recursive tree by repeatedly splitting branches.</p>'
        '<div class="controls"><button id="draw">Draw tree</button><input id="depth" type="range" min="1" max="8" value="5"></div>'
        '<canvas id="c" width="600" height="300"></canvas>'
        '<div id="status">Each branch calls itself with a smaller problem.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function branch(x, y, len, angle, depth) {
  if (depth === 0) return;
  const x2 = x + len * Math.cos(angle);
  const y2 = y + len * Math.sin(angle);
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
  branch(x2, y2, len * 0.7, angle - 0.4, depth - 1);
  branch(x2, y2, len * 0.7, angle + 0.4, depth - 1);
}
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const d = parseInt(document.getElementById('depth').value);
  branch(canvas.width / 2, canvas.height - 20, 60, -Math.PI / 2, d);
  document.getElementById('status').textContent = `Recursion depth: ${d}`;
}
document.getElementById('draw').onclick = draw;
document.getElementById('depth').oninput = draw;
draw();
""",
    )


def stacks():
    return base(
        "Why Stacks Exist",
        '<p>Push and pop values from a stack.</p>'
        '<div class="controls"><input id="val" type="text" placeholder="Value"><button id="push">Push</button><button id="pop">Pop</button></div>'
        '<canvas id="c" width="300" height="300"></canvas>'
        '<div id="status">Stack is LIFO: last in, first out.</div>',
        """
const stack = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeRect(100, 40, 100, 240);
  stack.forEach((v, i) => {
    ctx.fillStyle = '#90caf9'; ctx.fillRect(105, 270 - (i + 1) * 40, 90, 35); ctx.strokeRect(105, 270 - (i + 1) * 40, 90, 35);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(v, 150, 263 - i * 40);
  });
}
document.getElementById('push').onclick = () => { const v = document.getElementById('val').value; if (v && stack.length < 6) stack.push(v); draw(); };
document.getElementById('pop').onclick = () => { if (stack.length) { const v = stack.pop(); document.getElementById('status').textContent = `Popped: ${v}`; } draw(); };
draw();
""",
    )


def queues():
    return base(
        "Why Queues Exist",
        '<p>Enqueue and dequeue items fairly.</p>'
        '<div class="controls"><input id="val" type="text" placeholder="Value"><button id="enqueue">Enqueue</button><button id="dequeue">Dequeue</button></div>'
        '<canvas id="c" width="600" height="160"></canvas>'
        '<div id="status">Queue is FIFO: first in, first out.</div>',
        """
const q = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  q.forEach((v, i) => {
    ctx.fillStyle = '#c8e6c9'; ctx.fillRect(20 + i * 70, 50, 60, 50); ctx.strokeRect(20 + i * 70, 50, 60, 50);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(v, 50 + i * 70, 80);
  });
}
document.getElementById('enqueue').onclick = () => { const v = document.getElementById('val').value; if (v && q.length < 8) q.push(v); draw(); };
document.getElementById('dequeue').onclick = () => { if (q.length) { const v = q.shift(); document.getElementById('status').textContent = `Dequeued: ${v}`; } draw(); };
draw();
""",
    )


def schedulers():
    return base(
        "Why Schedulers Exist",
        '<p>Run tasks with round-robin scheduling.</p>'
        '<div class="controls"><button id="step">Step</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Scheduler shares CPU time among tasks.</div>',
        """
const tasks = [{name:'A',work:5},{name:'B',work:3},{name:'C',work:4}];
let current = 0;
const quantum = 1;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  tasks.forEach((t, i) => {
    ctx.fillStyle = i === current ? '#ffcc80' : '#e3f2fd';
    ctx.fillRect(40 + i * 180, 40, 120, 100);
    ctx.strokeRect(40 + i * 180, 40, 120, 100);
    ctx.fillStyle = '#333'; ctx.font = '20px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(t.name, 100 + i * 180, 80);
    ctx.font = '16px sans-serif'; ctx.fillText(`work: ${t.work}`, 100 + i * 180, 110);
  });
}
document.getElementById('step').onclick = () => {
  if (tasks.every(t => t.work <= 0)) { document.getElementById('status').textContent = 'All tasks complete.'; return; }
  while (tasks[current].work <= 0) current = (current + 1) % tasks.length;
  tasks[current].work -= quantum;
  document.getElementById('status').textContent = `Ran task ${tasks[current].name} for ${quantum} unit.`;
  current = (current + 1) % tasks.length;
  draw();
};
document.getElementById('reset').onclick = () => { tasks[0].work=5; tasks[1].work=3; tasks[2].work=4; current=0; draw(); };
draw();
""",
    )


def processes():
    return base(
        "Why Processes Exist",
        '<p>Two processes have isolated memory. Crash one, the other survives.</p>'
        '<div class="controls"><button id="crashA">Crash A</button><button id="crashB">Crash B</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Processes isolate memory so failures do not spread.</div>',
        """
let alive = {A: true, B: true};
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ['A','B'].forEach((p, i) => {
    ctx.fillStyle = alive[p] ? '#c8e6c9' : '#ffcdd2';
    ctx.fillRect(50 + i * 260, 50, 200, 140); ctx.strokeRect(50 + i * 260, 50, 200, 140);
    ctx.fillStyle = '#333'; ctx.font = '20px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Process ${p}`, 150 + i * 260, 90);
    ctx.font = '14px sans-serif'; ctx.fillText(alive[p] ? 'Memory: isolated' : 'CRASHED', 150 + i * 260, 120);
  });
}
document.getElementById('crashA').onclick = () => { alive.A = false; draw(); };
document.getElementById('crashB').onclick = () => { alive.B = false; draw(); };
document.getElementById('reset').onclick = () => { alive = {A:true,B:true}; draw(); };
draw();
""",
    )


def threads():
    return base(
        "Why Threads Exist",
        '<p>Multiple threads share the same memory space.</p>'
        '<div class="controls"><button id="step">Step</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Threads read and write shared memory.</div>',
        """
let shared = 0;
const threads = [{name:'T1',pc:0},{name:'T2',pc:0}];
let current = 0;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#fff9c4'; ctx.fillRect(200, 40, 200, 60); ctx.strokeRect(200, 40, 200, 60);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Shared counter: ${shared}`, 300, 75);
  threads.forEach((t, i) => {
    ctx.fillStyle = i === current ? '#ffcc80' : '#e3f2fd';
    ctx.fillRect(40 + i * 300, 130, 160, 70); ctx.strokeRect(40 + i * 300, 130, 160, 70);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.fillText(t.name, 120 + i * 300, 160);
    ctx.font = '12px sans-serif'; ctx.fillText(`pc: ${t.pc}`, 120 + i * 300, 180);
  });
}
document.getElementById('step').onclick = () => {
  const t = threads[current];
  t.pc++;
  if (t.pc % 2 === 0) shared++;
  current = (current + 1) % threads.length;
  draw();
};
document.getElementById('reset').onclick = () => { shared = 0; threads.forEach(t => t.pc = 0); current = 0; draw(); };
draw();
""",
    )


def locks():
    return base(
        "Why Locks Exist",
        '<p>Two threads increment a counter. Without a lock, updates are lost.</p>'
        '<div class="controls"><button id="race">Run without lock</button><button id="locked">Run with lock</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">A lock serializes access to shared state.</div>',
        """
let counter = 0;
let locked = false;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(msg) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = locked ? '#fff9c4' : '#e3f2fd'; ctx.fillRect(220, 60, 160, 80); ctx.strokeRect(220, 60, 160, 80);
  ctx.fillStyle = '#333'; ctx.font = '20px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Counter: ${counter}`, 300, 100);
  ctx.font = '14px sans-serif'; ctx.fillText(locked ? 'LOCK HELD' : 'lock free', 300, 125);
  document.getElementById('status').textContent = msg;
}
function increment(n, useLock) {
  for (let i = 0; i < n; i++) {
    if (useLock) { if (locked) { i--; continue; } locked = true; }
    const temp = counter;
    temp++; // simulated interleaving
    counter = temp;
    if (useLock) locked = false;
  }
}
document.getElementById('race').onclick = () => { counter = 0; increment(1000, false); increment(1000, false); draw(`Race result: ${counter} (expected 2000)`); };
document.getElementById('locked').onclick = () => { counter = 0; increment(1000, true); draw(`Locked result: ${counter}`); };
document.getElementById('reset').onclick = () => { counter = 0; draw('Reset.'); };
draw('Press a button to compare.');
""",
    )


def deadlocks():
    return base(
        "Why Deadlocks Happen",
        '<p>Two threads each hold one resource and wait for the other.</p>'
        '<div class="controls"><button id="step">Step</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="500" height="300"></canvas>'
        '<div id="status">A circular wait creates deadlock.</div>',
        """
const t1 = {x:150,y:80,hasR1:true,hasR2:false};
const t2 = {x:350,y:80,hasR1:false,hasR2:true};
const r1 = {x:150,y:220}; const r2 = {x:350,y:220};
let step = 0;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = t1.hasR1 ? '#66bb6a' : '#e0e0e0'; ctx.beginPath(); ctx.arc(r1.x, r1.y, 25, 0, Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = t2.hasR2 ? '#66bb6a' : '#e0e0e0'; ctx.beginPath(); ctx.arc(r2.x, r2.y, 25, 0, Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('R1', r1.x, r1.y+5); ctx.fillText('R2', r2.x, r2.y+5);
  ctx.fillStyle = '#90caf9'; ctx.fillRect(t1.x-30, t1.y-20, 60, 40); ctx.strokeRect(t1.x-30, t1.y-20, 60, 40); ctx.fillText('T1', t1.x, t1.y+5);
  ctx.fillStyle = '#90caf9'; ctx.fillRect(t2.x-30, t2.y-20, 60, 40); ctx.strokeRect(t2.x-30, t2.y-20, 60, 40); ctx.fillText('T2', t2.x, t2.y+5);
  if (t1.hasR1) { ctx.beginPath(); ctx.moveTo(t1.x, t1.y+20); ctx.lineTo(r1.x, r1.y-25); ctx.stroke(); }
  if (t2.hasR2) { ctx.beginPath(); ctx.moveTo(t2.x, t2.y+20); ctx.lineTo(r2.x, r2.y-25); ctx.stroke(); }
  if (step >= 1) { ctx.beginPath(); ctx.moveTo(t1.x+30, t1.y); ctx.lineTo(r2.x-25, r2.y); ctx.strokeStyle = '#ef5350'; ctx.stroke(); ctx.strokeStyle = '#000'; }
  if (step >= 2) { ctx.beginPath(); ctx.moveTo(t2.x-30, t2.y); ctx.lineTo(r1.x+25, r1.y); ctx.strokeStyle = '#ef5350'; ctx.stroke(); ctx.strokeStyle = '#000'; }
}
document.getElementById('step').onclick = () => { step = Math.min(step + 1, 2); if (step === 2) document.getElementById('status').textContent = 'Deadlock: each thread waits for the other.'; draw(); };
document.getElementById('reset').onclick = () => { step = 0; draw(); };
draw();
""",
    )


def virtual_memory():
    return base(
        "Why Virtual Memory Exists",
        '<p>Map virtual pages to physical frames.</p>'
        '<div class="controls"><button id="map">Map page 2 to frame 5</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="260"></canvas>'
        '<div id="status">Virtual addresses are translated to physical addresses.</div>',
        """
const pages = Array(8).fill(null);
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Virtual pages', 80, 30); ctx.fillText('Physical frames', 380, 30);
  pages.forEach((f, i) => {
    ctx.fillStyle = f !== null ? '#c8e6c9' : '#e3f2fd'; ctx.fillRect(60, 45 + i * 25, 140, 22); ctx.strokeRect(60, 45 + i * 25, 140, 22);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`page ${i}`, 130, 61 + i * 25);
    ctx.fillStyle = '#e3f2fd'; ctx.fillRect(360, 45 + i * 25, 140, 22); ctx.strokeRect(360, 45 + i * 25, 140, 22);
    ctx.fillStyle = '#333'; ctx.fillText(`frame ${i}`, 430, 61 + i * 25);
    if (f !== null) { ctx.beginPath(); ctx.moveTo(200, 56 + i * 25); ctx.lineTo(360, 56 + f * 25); ctx.strokeStyle = '#ef5350'; ctx.stroke(); ctx.strokeStyle = '#000'; }
  });
}
document.getElementById('map').onclick = () => { pages[2] = 5; document.getElementById('status').textContent = 'Virtual page 2 now maps to physical frame 5.'; draw(); };
document.getElementById('reset').onclick = () => { pages.fill(null); draw(); };
draw();
""",
    )


def context_switching():
    return base(
        "Why Context Switching Costs",
        '<p>Save one task state, restore another. More state means more cost.</p>'
        '<div class="controls"><button id="switch">Context switch</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Switching means saving and restoring registers, caches, and TLB.</div>',
        """
let active = 0;
const regs = [['r0:5','r1:3','pc:12'],['r0:9','r1:7','pc:44']];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  regs.forEach((r, i) => {
    ctx.fillStyle = i === active ? '#ffcc80' : '#e3f2fd';
    ctx.fillRect(60 + i * 280, 50, 180, 130); ctx.strokeRect(60 + i * 280, 50, 180, 130);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Task ${i+1}`, 150 + i * 280, 80);
    r.forEach((line, j) => { ctx.font = '14px sans-serif'; ctx.fillText(line, 150 + i * 280, 105 + j * 22); });
  });
}
async function switchTask() {
  document.getElementById('status').textContent = 'Saving task ' + (active+1) + ' state...';
  await new Promise(r => setTimeout(r, 500));
  active = (active + 1) % 2;
  document.getElementById('status').textContent = 'Restored task ' + (active+1) + ' state.';
  draw();
}
document.getElementById('switch').onclick = switchTask;
draw();
""",
    )


def files_arent_enough():
    return base(
        "Why Files Aren't Enough",
        '<p>Scan every line vs jump directly to a record.</p>'
        '<div class="controls"><button id="scan">Scan file</button><button id="jump">Use index</button></div>'
        '<canvas id="c" width="600" height="180"></canvas>'
        '<div id="status">Files force linear scans; databases use structures to jump.</div>',
        """
const records = Array.from({length: 20}, (_, i) => ({id: i*3, name: `user${i}`}));
const target = 33;
let mode = 'scan';
let current = 0;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1, found=false) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  records.forEach((r, i) => {
    ctx.fillStyle = i === hi ? (found ? '#66bb6a' : '#ffcc80') : '#e3f2fd';
    ctx.fillRect(10 + i * 28, 60, 25, 40); ctx.strokeRect(10 + i * 28, 60, 25, 40);
    ctx.fillStyle = '#333'; ctx.font = '9px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(r.id, 22 + i * 28, 85);
  });
}
async function runScan() {
  mode = 'scan';
  for (let i = 0; i < records.length; i++) {
    draw(i, records[i].id === target);
    document.getElementById('status').textContent = `Scanning record ${i}...`;
    await new Promise(r => setTimeout(r, 80));
    if (records[i].id === target) return;
  }
}
async function runIndex() {
  mode = 'index';
  const idx = records.findIndex(r => r.id === target);
  draw(idx, true);
  document.getElementById('status').textContent = `Index lookup: found at position ${idx} in one step.`;
}
document.getElementById('scan').onclick = runScan;
document.getElementById('jump').onclick = runIndex;
draw();
""",
    )


def indexes_exist():
    return base(
        "Why Indexes Exist",
        '<p>Use an index to find a row without scanning the table.</p>'
        '<div class="controls"><input id="q" type="number" value="42"><button id="search">Search</button></div>'
        '<canvas id="c" width="700" height="220"></canvas>'
        '<div id="status">Indexes turn full-table scans into direct lookups.</div>',
        """
const rows = Array.from({length: 15}, (_, i) => ({id: i*2, data: `row${i}`}));
const index = Object.fromEntries(rows.map(r => [r.id, r]));
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1, found=false) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Table', 20, 25);
  rows.forEach((r, i) => {
    ctx.fillStyle = i === hi ? (found ? '#66bb6a' : '#ffcc80') : '#e3f2fd';
    ctx.fillRect(20 + i * 44, 40, 40, 30); ctx.strokeRect(20 + i * 44, 40, 40, 30);
    ctx.fillStyle = '#333'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(r.id, 40 + i * 44, 59);
  });
}
document.getElementById('search').onclick = () => {
  const q = parseInt(document.getElementById('q').value);
  const idx = rows.findIndex(r => r.id === q);
  draw(idx, idx >= 0);
  document.getElementById('status').textContent = idx >= 0 ? `Index found ${q} at table position ${idx}.` : `${q} not found.`;
};
draw();
""",
    )


def btrees_won():
    return base(
        "Why B-Trees Won",
        '<p>A B-tree keeps many keys in each node to match disk block size.</p>'
        '<div class="controls"><button id="insert">Insert</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="700" height="280"></canvas>'
        '<div id="status">B-tree nodes group keys so one disk read covers many.</div>',
        """
let root = {keys:[], children:[], leaf:true};
const order = 3;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function drawNode(n, x, y, gap) {
  const w = Math.max(40, n.keys.length * 35 + 10);
  ctx.fillStyle = '#e3f2fd'; ctx.fillRect(x - w/2, y - 18, w, 36); ctx.strokeRect(x - w/2, y - 18, w, 36);
  ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.keys.join(' | '), x, y + 4);
  if (!n.leaf) {
    n.children.forEach((c, i) => {
      const cx = x - gap/2 + i * gap / Math.max(1, n.children.length - 1);
      ctx.beginPath(); ctx.moveTo(x - w/2 + (i+1)*(w/(n.children.length+1)), y + 18); ctx.lineTo(cx, y + 60); ctx.stroke();
      drawNode(c, cx, y + 60, gap/2);
    });
  }
}
function insert(v) {
  if (!root.keys.length) { root.keys.push(v); return; }
  let n = root;
  while (!n.leaf) {
    let i = 0; while (i < n.keys.length && v > n.keys[i]) i++;
    n = n.children[i];
  }
  n.keys.push(v); n.keys.sort((a,b)=>a-b);
}
document.getElementById('insert').onclick = () => {
  const v = Math.floor(Math.random() * 100);
  insert(v);
  document.getElementById('status').textContent = `Inserted ${v}.`;
  draw();
};
document.getElementById('reset').onclick = () => { root = {keys:[], children:[], leaf:true}; draw(); };
function draw() { ctx.clearRect(0, 0, canvas.width, canvas.height); drawNode(root, canvas.width/2, 40, 300); }
[10,20,5,30,40,25].forEach(insert);
draw();
""",
    )


def transactions():
    return base(
        "Why Transactions Exist",
        '<p>Transfer balance between accounts. A crash mid-update needs rollback.</p>'
        '<div class="controls"><button id="commit">Commit transfer</button><button id="crash">Simulate crash</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="500" height="220"></canvas>'
        '<div id="status">Transactions commit atomically or roll back.</div>',
        """
let a = 100, b = 50;
let tempA, tempB;
let state = 'ready';
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = state === 'crash' ? '#ffcdd2' : '#e3f2fd';
  ctx.fillRect(60, 50, 140, 100); ctx.strokeRect(60, 50, 140, 100);
  ctx.fillStyle = state === 'crash' ? '#ffcdd2' : '#e3f2fd';
  ctx.fillRect(300, 50, 140, 100); ctx.strokeRect(300, 50, 140, 100);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Account A', 130, 85); ctx.fillText(state === 'crash' ? a : a, 130, 115);
  ctx.fillText('Account B', 370, 85); ctx.fillText(state === 'crash' ? b : b, 370, 115);
  ctx.font = '12px sans-serif'; ctx.fillText(state === 'crash' ? 'rolled back' : 'committed', 250, 180);
}
document.getElementById('commit').onclick = () => { a -= 20; b += 20; state = 'committed'; draw(); };
document.getElementById('crash').onclick = () => { state = 'crash'; draw(); };
document.getElementById('reset').onclick = () => { a = 100; b = 50; state = 'ready'; draw(); };
draw();
""",
    )


def mvcc():
    return base(
        "Why MVCC Exists",
        '<p>A reader sees a snapshot while a writer creates a new version.</p>'
        '<div class="controls"><button id="write">Writer updates</button><button id="read">Reader reads snapshot</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">MVCC lets readers and writers proceed without blocking.</div>',
        """
let current = 10;
const versions = [{value:10, tx:1}];
let nextTx = 2;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  versions.forEach((v, i) => {
    ctx.fillStyle = i === versions.length - 1 ? '#c8e6c9' : '#fff9c4';
    ctx.fillRect(40 + i * 120, 80, 100, 60); ctx.strokeRect(40 + i * 120, 80, 100, 60);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`tx ${v.tx}`, 90 + i * 120, 105); ctx.fillText(`value ${v.value}`, 90 + i * 120, 130);
  });
}
document.getElementById('write').onclick = () => {
  current += 5;
  versions.push({value: current, tx: nextTx++});
  document.getElementById('status').textContent = `Writer created new version ${current}.`;
  draw();
};
document.getElementById('read').onclick = () => {
  const snap = versions[0];
  document.getElementById('status').textContent = `Reader sees snapshot tx ${snap.tx}: value ${snap.value} (unchanged).`;
};
draw();
""",
    )


def query_planners():
    return base(
        "Why Query Planners Matter",
        '<p>Choose between a full scan and an index seek for the same query.</p>'
        '<div class="controls"><button id="scan">Plan: full scan</button><button id="seek">Plan: index seek</button></div>'
        '<canvas id="c" width="600" height="180"></canvas>'
        '<div id="status">A good planner picks the cheaper execution strategy.</div>',
        """
const rows = Array.from({length: 30}, (_, i) => i);
const target = 24;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1, found=false, cost=0) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  rows.forEach((r, i) => {
    ctx.fillStyle = i === hi ? (found ? '#66bb6a' : '#ffcc80') : '#e3f2fd';
    ctx.fillRect(15 + i * 19, 60, 16, 30); ctx.strokeRect(15 + i * 19, 60, 16, 30);
    ctx.fillStyle = '#333'; ctx.font = '8px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(r, 23 + i * 19, 80);
  });
  document.getElementById('status').textContent = `Cost: ${cost} rows examined.`;
}
async function scan() {
  for (let i = 0; i < rows.length; i++) {
    draw(i, rows[i] === target, i + 1);
    await new Promise(r => setTimeout(r, 60));
    if (rows[i] === target) return;
  }
}
function seek() {
  const idx = rows.indexOf(target);
  draw(idx, true, 1);
}
document.getElementById('scan').onclick = scan;
document.getElementById('seek').onclick = seek;
draw();
""",
    )


def computers_need_addresses():
    return base(
        "Why Computers Need Addresses",
        '<p>Route a packet from source to destination using addresses.</p>'
        '<div class="controls"><input id="dest" type="number" min="1" max="4" value="4" style="width:80px"><button id="send">Send</button></div>'
        '<canvas id="c" width="500" height="300"></canvas>'
        '<div id="status">Addresses let routers decide where to forward packets.</div>',
        """
const nodes = [{id:1,x:80,y:150},{id:2,x:250,y:80},{id:3,x:250,y:220},{id:4,x:420,y:150}];
const links = [[1,2],[1,3],[2,4],[3,4]];
let packet = null;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  links.forEach(([a,b]) => { const u = nodes.find(n=>n.id===a), v = nodes.find(n=>n.id===b); ctx.beginPath(); ctx.moveTo(u.x, u.y); ctx.lineTo(v.x, v.y); ctx.stroke(); });
  nodes.forEach(n => { ctx.beginPath(); ctx.arc(n.x, n.y, 25, 0, Math.PI*2); ctx.fillStyle = '#e3f2fd'; ctx.fill(); ctx.stroke(); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.id, n.x, n.y+5); ctx.font = '10px sans-serif'; ctx.fillText(`10.0.0.${n.id}`, n.x, n.y+38); });
  if (packet) { ctx.beginPath(); ctx.arc(packet.x, packet.y, 8, 0, Math.PI*2); ctx.fillStyle = '#ef5350'; ctx.fill(); }
}
async function send() {
  const dest = parseInt(document.getElementById('dest').value);
  packet = {...nodes[0]};
  const path = [1, dest <= 2 ? 2 : 3, dest];
  for (let i = 0; i < path.length - 1; i++) {
    const a = nodes.find(n=>n.id===path[i]), b = nodes.find(n=>n.id===path[i+1]);
    for (let t = 0; t <= 1; t += 0.05) { packet.x = a.x + (b.x-a.x)*t; packet.y = a.y + (b.y-a.y)*t; draw(); await new Promise(r => setTimeout(r, 30)); }
  }
  document.getElementById('status').textContent = `Packet delivered to 10.0.0.${dest}.`;
}
document.getElementById('send').onclick = send;
draw();
""",
    )


def packets_exist():
    return base(
        "Why Packets Exist",
        '<p>Split a large message into packets and reassemble at the destination.</p>'
        '<div class="controls"><button id="split">Split & send</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Packets travel independently and are reassembled.</div>',
        """
const msg = ['H','e','l','l','o'];
let packets = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Source', 30, 30); ctx.fillText('Destination', 480, 30);
  packets.forEach((p, i) => {
    ctx.fillStyle = '#90caf9'; ctx.fillRect(p.x, 80 + i * 20, 30, 16); ctx.strokeRect(p.x, 80 + i * 20, 30, 16);
    ctx.fillStyle = '#333'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(p.ch, p.x + 15, 92 + i * 20);
  });
}
async function split() {
  packets = msg.map((ch, i) => ({ch, x: 30, y: 80 + i * 20}));
  draw();
  for (let i = 0; i < packets.length; i++) {
    for (let x = 30; x <= 480; x += 10) { packets[i].x = x; draw(); await new Promise(r => setTimeout(r, 20)); }
  }
  document.getElementById('status').textContent = 'Message reassembled: ' + msg.join('');
}
document.getElementById('split').onclick = split;
draw();
""",
    )


def tcp_exists():
    return base(
        "Why TCP Exists",
        '<p>Send packets with sequence numbers. Lost packets are retransmitted.</p>'
        '<div class="controls"><button id="send">Send with loss</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">TCP uses sequence numbers and ACKs to recover from loss.</div>',
        """
let packets = [{seq:1,sent:false,lost:false,acked:false},{seq:2,sent:false,lost:true,acked:false},{seq:3,sent:false,lost:false,acked:false}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Sender', 40, 30); ctx.fillText('Receiver', 480, 30);
  packets.forEach((p, i) => {
    const x = p.sent ? (p.lost ? 280 : 520) : 50;
    const y = 70 + i * 40;
    ctx.fillStyle = p.lost ? '#ffcdd2' : (p.acked ? '#c8e6c9' : '#90caf9');
    ctx.fillRect(x, y, 50, 26); ctx.strokeRect(x, y, 50, 26);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`seq ${p.seq}`, x + 25, y + 17);
  });
}
async function send() {
  packets.forEach(p => { p.sent = false; p.acked = false; });
  for (let p of packets) {
    p.sent = true;
    draw();
    await new Promise(r => setTimeout(r, 400));
    if (p.lost) { document.getElementById('status').textContent = `Packet ${p.seq} lost. Retransmitting...`; await new Promise(r => setTimeout(r, 600)); p.lost = false; }
    p.acked = true;
    draw();
    await new Promise(r => setTimeout(r, 300));
  }
  document.getElementById('status').textContent = 'All packets acknowledged.';
}
document.getElementById('send').onclick = send;
draw();
""",
    )


def congestion():
    return base(
        "Why Congestion Happens",
        '<p>Increase the sending window until packets drop, then back off.</p>'
        '<div class="controls"><button id="step">Step</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Congestion control probes for available bandwidth.</div>',
        """
let window = 1;
let drops = 0;
const capacity = 8;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e0e0e0'; ctx.fillRect(50, 140, 500, 30);
  ctx.fillStyle = window > capacity ? '#ef5350' : '#90caf9'; ctx.fillRect(50, 140, Math.min(window, capacity) / capacity * 500, 30); ctx.strokeRect(50, 140, 500, 30);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'left'; ctx.fillText(`Window: ${window}`, 50, 80); ctx.fillText(`Capacity: ${capacity}`, 50, 105); ctx.fillText(`Drops: ${drops}`, 50, 130);
}
document.getElementById('step').onclick = () => {
  if (window > capacity) { drops++; window = Math.max(1, Math.floor(window / 2)); }
  else window++;
  draw();
};
document.getElementById('reset').onclick = () => { window = 1; drops = 0; draw(); };
draw();
""",
    )


def load_balancers():
    return base(
        "Why Load Balancers Exist",
        '<p>Distribute requests across backends.</p>'
        '<div class="controls"><button id="send">Send requests</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Load balancers spread traffic and hide backend failures.</div>',
        """
const backends = [{id:1,load:0,alive:true},{id:2,load:0,alive:true},{id:3,load:0,alive:true}];
let current = 0;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e3f2fd'; ctx.fillRect(250, 30, 100, 40); ctx.strokeRect(250, 30, 100, 40); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('LB', 300, 55);
  backends.forEach((b, i) => {
    ctx.fillStyle = b.alive ? '#c8e6c9' : '#ffcdd2';
    ctx.fillRect(100 + i * 160, 120, 120, 50); ctx.strokeRect(100 + i * 160, 120, 120, 50);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Backend ${b.id}`, 160 + i * 160, 145); ctx.fillText(`load ${b.load}`, 160 + i * 160, 162);
    ctx.beginPath(); ctx.moveTo(300, 70); ctx.lineTo(160 + i * 160, 120); ctx.stroke();
  });
}
document.getElementById('send').onclick = () => {
  const alive = backends.filter(b => b.alive);
  const b = alive[current % alive.length];
  b.load++;
  current++;
  draw();
};
draw();
""",
    )


def one_computer():
    return base(
        "Why One Computer Isn't Enough",
        '<p>Partition data across nodes when one machine overflows.</p>'
        '<div class="controls"><button id="add">Add data</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Partitioning spreads data across machines.</div>',
        """
const nodes = [{id:1,items:[]},{id:2,items:[]},{id:3,items:[]}];
let next = 1;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  nodes.forEach((n, i) => {
    ctx.fillStyle = '#e3f2fd'; ctx.fillRect(60 + i * 180, 60, 140, 100); ctx.strokeRect(60 + i * 180, 60, 140, 100);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Node ${n.id}`, 130 + i * 180, 90);
    ctx.fillText(`${n.items.length} items`, 130 + i * 180, 115);
  });
}
document.getElementById('add').onclick = () => {
  const n = nodes[(next - 1) % nodes.length];
  n.items.push(next++);
  draw();
};
document.getElementById('reset').onclick = () => { nodes.forEach(n => n.items = []); next = 1; draw(); };
draw();
""",
    )


def clocks_lie():
    return base(
        "Why Clocks Lie",
        '<p>Three machines measure the same event with slightly different clocks.</p>'
        '<div class="controls"><button id="tick">Tick</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Clock skew makes ordering events across machines hard.</div>',
        """
const clocks = [{name:'A',time:0,drift:1},{name:'B',time:0,drift:1.1},{name:'C',time:0,drift:0.9}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  clocks.forEach((c, i) => {
    ctx.fillStyle = '#e3f2fd'; ctx.fillRect(60 + i * 180, 60, 140, 80); ctx.strokeRect(60 + i * 180, 60, 140, 80);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(c.name, 130 + i * 180, 90); ctx.fillText(c.time.toFixed(1), 130 + i * 180, 120);
  });
}
document.getElementById('tick').onclick = () => { clocks.forEach(c => c.time += c.drift); draw(); };
document.getElementById('reset').onclick = () => { clocks.forEach(c => c.time = 0); draw(); };
draw();
""",
    )


def consensus():
    return base(
        "Why Consensus Exists",
        '<p>Three nodes vote on a value. A majority wins even if one fails.</p>'
        '<div class="controls"><button id="propose">Propose value</button><button id="fail">Fail node 3</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="500" height="220"></canvas>'
        '<div id="status">Consensus requires a quorum of agreeing nodes.</div>',
        """
const nodes = [{id:1,alive:true,vote:null},{id:2,alive:true,vote:null},{id:3,alive:true,vote:null}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  nodes.forEach((n, i) => {
    ctx.fillStyle = n.alive ? (n.vote ? '#c8e6c9' : '#e3f2fd') : '#ffcdd2';
    ctx.fillRect(60 + i * 140, 80, 100, 80); ctx.strokeRect(60 + i * 140, 80, 100, 80);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Node ${n.id}`, 110 + i * 140, 110); ctx.fillText(n.vote || '—', 110 + i * 140, 140);
  });
}
document.getElementById('propose').onclick = () => {
  nodes.forEach(n => { if (n.alive) n.vote = 'X'; });
  const votes = nodes.filter(n => n.vote === 'X').length;
  document.getElementById('status').textContent = votes >= 2 ? 'Consensus reached.' : 'No quorum.';
  draw();
};
document.getElementById('fail').onclick = () => { nodes[2].alive = false; nodes[2].vote = null; draw(); };
document.getElementById('reset').onclick = () => { nodes.forEach(n => { n.alive = true; n.vote = null; }); draw(); };
draw();
""",
    )


def raft():
    return base(
        "Why Raft Works",
        '<p>Hold a leader election among three nodes.</p>'
        '<div class="controls"><button id="elect">Start election</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="500" height="220"></canvas>'
        '<div id="status">Raft elects one leader to coordinate log replication.</div>',
        """
const nodes = [{id:1,state:'follower'},{id:2,state:'follower'},{id:3,state:'follower'}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  nodes.forEach((n, i) => {
    const color = n.state === 'leader' ? '#c8e6c9' : (n.state === 'candidate' ? '#ffcc80' : '#e3f2fd');
    ctx.fillStyle = color; ctx.fillRect(60 + i * 140, 80, 100, 80); ctx.strokeRect(60 + i * 140, 80, 100, 80);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Node ${n.id}`, 110 + i * 140, 110); ctx.fillText(n.state, 110 + i * 140, 140);
  });
}
document.getElementById('elect').onclick = () => {
  nodes.forEach(n => n.state = 'candidate');
  const leader = Math.floor(Math.random() * 3);
  nodes[leader].state = 'leader';
  nodes.forEach((n, i) => { if (i !== leader) n.state = 'follower'; });
  document.getElementById('status').textContent = `Node ${leader+1} became leader.`;
  draw();
};
document.getElementById('reset').onclick = () => { nodes.forEach(n => n.state = 'follower'); draw(); };
draw();
""",
    )


def eventual_consistency():
    return base(
        "Why Eventual Consistency Exists",
        '<p>Two replicas start with different values and converge.</p>'
        '<div class="controls"><button id="reconcile">Reconcile</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="500" height="200"></canvas>'
        '<div id="status">Replicas exchange updates until they agree.</div>',
        """
const replicas = [{id:1,value:3},{id:2,value:7}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  replicas.forEach((r, i) => {
    ctx.fillStyle = r.value === replicas[0].value && r.value === replicas[1].value ? '#c8e6c9' : '#ffcc80';
    ctx.fillRect(80 + i * 250, 70, 120, 80); ctx.strokeRect(80 + i * 250, 70, 120, 80);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Replica ${r.id}`, 140 + i * 250, 105); ctx.fillText(`value: ${r.value}`, 140 + i * 250, 135);
  });
}
document.getElementById('reconcile').onclick = () => {
  const max = Math.max(...replicas.map(r => r.value));
  replicas.forEach(r => r.value = max);
  document.getElementById('status').textContent = 'Replicas converged to ' + max + '.';
  draw();
};
document.getElementById('reset').onclick = () => { replicas[0].value = 3; replicas[1].value = 7; draw(); };
draw();
""",
    )


def distributed_transactions():
    return base(
        "Why Distributed Transactions Hurt",
        '<p>Two-phase commit blocks until all participants agree.</p>'
        '<div class="controls"><button id="prepare">Prepare</button><button id="commit">Commit</button><button id="abort">Abort</button></div>'
        '<canvas id="c" width="500" height="220"></canvas>'
        '<div id="status">Coordination adds latency and a single point of hesitation.</div>',
        """
const nodes = [{id:1,state:'ready'},{id:2,state:'ready'},{id:3,state:'uncertain'}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e3f2fd'; ctx.fillRect(200, 30, 100, 40); ctx.strokeRect(200, 30, 100, 40); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Coordinator', 250, 55);
  nodes.forEach((n, i) => {
    ctx.fillStyle = n.state === 'committed' ? '#c8e6c9' : (n.state === 'aborted' ? '#ffcdd2' : '#ffcc80');
    ctx.fillRect(60 + i * 140, 120, 100, 70); ctx.strokeRect(60 + i * 140, 120, 100, 70);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Node ${n.id}`, 110 + i * 140, 150); ctx.fillText(n.state, 110 + i * 140, 175);
  });
}
document.getElementById('prepare').onclick = () => { nodes.forEach(n => { if (n.state !== 'uncertain') n.state = 'prepared'; }); draw(); };
document.getElementById('commit').onclick = () => { if (nodes.every(n => n.state === 'prepared')) nodes.forEach(n => n.state = 'committed'); draw(); };
document.getElementById('abort').onclick = () => { nodes.forEach(n => n.state = 'aborted'); draw(); };
draw();
""",
    )


def caches_exist():
    return base(
        "Why Caches Exist",
        '<p>Store hot data close to the consumer.</p>'
        '<div class="controls"><button id="request">Request key</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Cache hits avoid slow backend lookups.</div>',
        """
const backend = {a:1,b:2,c:3,d:4,e:5};
const cache = {};
const hotKeys = ['a','a','b','a','c','a'];
let idx = 0;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hit, key) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#e3f2fd'; ctx.fillRect(80, 60, 160, 80); ctx.strokeRect(80, 60, 160, 80); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Cache', 160, 90); ctx.fillText(Object.keys(cache).join(', ') || 'empty', 160, 115);
  ctx.fillStyle = '#c8e6c9'; ctx.fillRect(360, 60, 160, 80); ctx.strokeRect(360, 60, 160, 80); ctx.fillStyle = '#333'; ctx.fillText('Backend', 440, 90);
  ctx.beginPath(); ctx.moveTo(240, 100); ctx.lineTo(360, 100); ctx.strokeStyle = hit ? '#66bb6a' : '#ef5350'; ctx.stroke(); ctx.strokeStyle = '#000';
  document.getElementById('status').textContent = `Request ${key}: ${hit ? 'cache hit' : 'cache miss'}.`;
}
document.getElementById('request').onclick = () => {
  const key = hotKeys[idx % hotKeys.length];
  const hit = key in cache;
  if (!hit) cache[key] = backend[key];
  draw(hit, key);
  idx++;
};
document.getElementById('reset').onclick = () => { Object.keys(cache).forEach(k => delete cache[k]); idx = 0; draw(false, '-'); };
draw(false, '-');
""",
    )


def cdns():
    return base(
        "Why CDNs Exist",
        '<p>Route users to the nearest edge server.</p>'
        '<div class="controls"><button id="request">Request from user</button></div>'
        '<canvas id="c" width="600" height="260"></canvas>'
        '<div id="status">CDNs reduce latency by serving content from nearby edges.</div>',
        """
const user = {x:80,y:200};
const edges = [{x:200,y:80},{x:420,y:100}];
const origin = {x:300,y:220};
let lastEdge = null;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath(); ctx.arc(user.x, user.y, 12, 0, Math.PI*2); ctx.fillStyle = '#90caf9'; ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('User', user.x, user.y + 28);
  edges.forEach(e => { ctx.beginPath(); ctx.arc(e.x, e.y, 15, 0, Math.PI*2); ctx.fillStyle = '#c8e6c9'; ctx.fill(); ctx.stroke(); ctx.fillText('Edge', e.x, e.y + 28); });
  ctx.beginPath(); ctx.arc(origin.x, origin.y, 18, 0, Math.PI*2); ctx.fillStyle = '#ffcc80'; ctx.fill(); ctx.stroke(); ctx.fillText('Origin', origin.x, origin.y + 32);
  if (lastEdge) { ctx.beginPath(); ctx.moveTo(user.x, user.y); ctx.lineTo(lastEdge.x, lastEdge.y); ctx.strokeStyle = '#1976d2'; ctx.stroke(); ctx.strokeStyle = '#000'; }
}
document.getElementById('request').onclick = () => {
  const d1 = Math.hypot(user.x - edges[0].x, user.y - edges[0].y);
  const d2 = Math.hypot(user.x - edges[1].x, user.y - edges[1].y);
  lastEdge = d1 < d2 ? edges[0] : edges[1];
  document.getElementById('status').textContent = `Routed to nearest edge.`;
  draw();
};
draw();
""",
    )


def message_queues():
    return base(
        "Why Queues Exist",
        '<p>Publish messages to a queue; consumers process them at their own pace.</p>'
        '<div class="controls"><button id="publish">Publish</button><button id="consume">Consume</button></div>'
        '<canvas id="c" width="600" height="180"></canvas>'
        '<div id="status">Queues decouple producers and consumers.</div>',
        """
const queue = [];
let nextMsg = 1;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Producer', 30, 60); ctx.fillText('Consumer', 500, 60);
  ctx.fillStyle = '#fff9c4'; ctx.fillRect(180, 70, 240, 50); ctx.strokeRect(180, 70, 240, 50);
  queue.forEach((m, i) => {
    ctx.fillStyle = '#90caf9'; ctx.fillRect(190 + i * 45, 78, 38, 34); ctx.strokeRect(190 + i * 45, 78, 38, 34);
    ctx.fillStyle = '#333'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(m, 209 + i * 45, 98);
  });
}
document.getElementById('publish').onclick = () => { if (queue.length < 5) queue.push(`m${nextMsg++}`); draw(); };
document.getElementById('consume').onclick = () => { if (queue.length) { const m = queue.shift(); document.getElementById('status').textContent = `Consumed ${m}.`; } draw(); };
draw();
""",
    )


def sharding():
    return base(
        "Why Sharding Exists",
        '<p>Route records to shards by key hash.</p>'
        '<div class="controls"><input id="key" type="text" value="user123"><button id="route">Route</button></div>'
        '<canvas id="c" width="600" height="200"></canvas>'
        '<div id="status">Sharding partitions data by key across nodes.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function hash(s) { let h = 0; for (let c of s) h = (h * 31 + c.charCodeAt(0)) % 3; return h; }
function draw(shard=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < 3; i++) {
    ctx.fillStyle = i === shard ? '#ffcc80' : '#e3f2fd';
    ctx.fillRect(60 + i * 180, 70, 140, 100); ctx.strokeRect(60 + i * 180, 70, 140, 100);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(`Shard ${i}`, 130 + i * 180, 115);
  }
}
document.getElementById('route').onclick = () => {
  const k = document.getElementById('key').value;
  const s = hash(k);
  document.getElementById('status').textContent = `Key "${k}" routes to shard ${s}.`;
  draw(s);
};
draw();
""",
    )


def replication():
    return base(
        "Why Replication Exists",
        '<p>A leader writes; followers replicate the write.</p>'
        '<div class="controls"><button id="write">Write</button><button id="fail">Fail leader</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Replication provides durability and failover.</div>',
        """
const nodes = [{id:'leader',value:0,alive:true},{id:'follower1',value:0,alive:true},{id:'follower2',value:0,alive:true}];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  nodes.forEach((n, i) => {
    ctx.fillStyle = n.alive ? (i === 0 ? '#ffcc80' : '#e3f2fd') : '#ffcdd2';
    ctx.fillRect(60 + i * 180, 70, 140, 100); ctx.strokeRect(60 + i * 180, 70, 140, 100);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n.id, 130 + i * 180, 105); ctx.fillText(`value: ${n.value}`, 130 + i * 180, 135);
  });
}
document.getElementById('write').onclick = () => {
  if (nodes[0].alive) { nodes.forEach(n => { if (n.alive) n.value++; }); }
  draw();
};
document.getElementById('fail').onclick = () => { nodes[0].alive = false; draw(); };
document.getElementById('reset').onclick = () => { nodes.forEach(n => { n.alive = true; n.value = 0; }); draw(); };
draw();
""",
    )


def search_engines():
    return base(
        "Why Search Engines Exist",
        '<p>Build an inverted index and query it.</p>'
        '<div class="controls"><input id="q" type="text" value="cat" style="width:100px"><button id="query">Query</button></div>'
        '<canvas id="c" width="600" height="240"></canvas>'
        '<div id="status">Inverted indexes map terms to documents.</div>',
        """
const docs = [{id:1,text:'the cat sat'},{id:2,text:'the dog ran'},{id:3,text:'cat and dog'}];
const index = {};
docs.forEach(d => d.text.split(' ').forEach(w => { if (!index[w]) index[w] = new Set(); index[w].add(d.id); }));
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(q, results) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Documents', 30, 30);
  docs.forEach((d, i) => { ctx.fillStyle = results.includes(d.id) ? '#c8e6c9' : '#e3f2fd'; ctx.fillRect(30, 45 + i * 45, 250, 35); ctx.strokeRect(30, 45 + i * 45, 250, 35); ctx.fillStyle = '#333'; ctx.fillText(`${d.id}: ${d.text}`, 40, 68 + i * 45); });
  ctx.fillText('Index', 320, 30);
  Object.keys(index).forEach((w, i) => { ctx.fillStyle = w === q ? '#ffcc80' : '#fff9c4'; ctx.fillRect(320, 45 + i * 35, 200, 28); ctx.strokeRect(320, 45 + i * 35, 200, 28); ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.fillText(`${w} → [${[...index[w]].join(', ')}]`, 330, 64 + i * 35); });
}
document.getElementById('query').onclick = () => {
  const q = document.getElementById('q').value;
  const results = index[q] ? [...index[q]] : [];
  document.getElementById('status').textContent = `Query "${q}" returned documents: [${results.join(', ')}]`;
  draw(q, results);
};
draw('', []);
""",
    )


def gpus():
    return base(
        "Why GPUs Changed Everything",
        '<p>Run many parallel workers on a grid.</p>'
        '<div class="controls"><button id="run">Run parallel</button></div>'
        '<canvas id="c" width="500" height="300"></canvas>'
        '<div id="status">GPUs launch thousands of lightweight threads at once.</div>',
        """
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const cols = 10, rows = 10;
let active = [];
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      ctx.fillStyle = active.some(a => a.x === x && a.y === y) ? '#66bb6a' : '#e3f2fd';
      ctx.fillRect(40 + x * 42, 40 + y * 22, 38, 18); ctx.strokeRect(40 + x * 42, 40 + y * 22, 38, 18);
    }
  }
}
async function run() {
  active = [];
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) { active.push({x, y}); }
    draw();
    document.getElementById('status').textContent = `Launched ${active.length} threads.`;
    await new Promise(r => setTimeout(r, 50));
  }
}
document.getElementById('run').onclick = run;
draw();
""",
    )


def matmul():
    return base(
        "Why Matrix Multiplication Matters",
        '<p>Multiply a row vector by a column vector.</p>'
        '<div class="controls"><button id="compute">Compute dot product</button></div>'
        '<canvas id="c" width="500" height="220"></canvas>'
        '<div id="status">Neural networks are built from many such multiplications.</div>',
        """
const a = [1,2,3], b = [4,5,6];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(hi=-1) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  a.forEach((v, i) => {
    ctx.fillStyle = i === hi ? '#ffcc80' : '#90caf9'; ctx.fillRect(60, 50 + i * 40, 40, 30); ctx.strokeRect(60, 50 + i * 40, 40, 30); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(v, 80, 70 + i * 40);
    ctx.fillStyle = i === hi ? '#ffcc80' : '#c8e6c9'; ctx.fillRect(180, 50 + i * 40, 40, 30); ctx.strokeRect(180, 50 + i * 40, 40, 30); ctx.fillText(b[i], 200, 70 + i * 40);
  });
  ctx.fillStyle = '#333'; ctx.font = '18px sans-serif'; ctx.textAlign = 'left'; ctx.fillText(`Result: ${a.reduce((s,v,i)=>s+v*b[i],0)}`, 280, 110);
}
async function compute() {
  let sum = 0;
  for (let i = 0; i < a.length; i++) { draw(i); sum += a[i] * b[i]; document.getElementById('status').textContent = `sum += ${a[i]} * ${b[i]} = ${sum}`; await new Promise(r => setTimeout(r, 500)); }
  draw(-1);
}
document.getElementById('compute').onclick = compute;
draw();
""",
    )


def attention():
    return base(
        "Why Attention Exists",
        '<p>Compute attention scores between query and keys.</p>'
        '<div class="controls"><button id="score">Compute scores</button></div>'
        '<canvas id="c" width="500" height="260"></canvas>'
        '<div id="status">Attention weights show which tokens matter most.</div>',
        """
const tokens = ['The','cat','sat'];
const query = [0.5, 0.3, 0.2];
const keys = [[0.4,0.4,0.2],[0.2,0.7,0.1],[0.3,0.3,0.4]];
let scores = [0,0,0];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  tokens.forEach((t, i) => {
    ctx.fillStyle = '#e3f2fd'; ctx.fillRect(60, 40 + i * 70, 80, 40); ctx.strokeRect(60, 40 + i * 70, 80, 40);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(t, 100, 65 + i * 70);
    ctx.fillStyle = `rgba(239,83,80,${scores[i]})`; ctx.fillRect(180, 40 + i * 70, 60, 40); ctx.strokeRect(180, 40 + i * 70, 60, 40);
    ctx.fillStyle = '#333'; ctx.fillText(scores[i].toFixed(2), 210, 65 + i * 70);
  });
}
function dot(a,b) { return a.reduce((s,v,i)=>s+v*b[i],0); }
document.getElementById('score').onclick = () => {
  scores = keys.map(k => Math.max(0, dot(query, k)));
  const sum = scores.reduce((a,b)=>a+b,0);
  scores = scores.map(s => sum ? s/sum : 0);
  document.getElementById('status').textContent = 'Softmax scores computed.';
  draw();
};
draw();
""",
    )


def transformers_scale():
    return base(
        "Why Transformers Scale",
        '<p>Process all tokens in parallel instead of one by one.</p>'
        '<div class="controls"><button id="parallel">Parallel pass</button><button id="serial">Serial pass</button></div>'
        '<canvas id="c" width="600" height="160"></canvas>'
        '<div id="status">Transformers replace recurrence with parallel self-attention.</div>',
        """
const tokens = ['t1','t2','t3','t4','t5'];
let highlights = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  tokens.forEach((t, i) => {
    ctx.fillStyle = highlights.includes(i) ? '#66bb6a' : '#e3f2fd';
    ctx.fillRect(60 + i * 100, 50, 70, 50); ctx.strokeRect(60 + i * 100, 50, 70, 50);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(t, 95 + i * 100, 80);
  });
}
async function parallel() { highlights = tokens.map((_,i)=>i); draw(); document.getElementById('status').textContent = 'All tokens processed in parallel.'; }
async function serial() {
  for (let i = 0; i < tokens.length; i++) { highlights = [i]; draw(); document.getElementById('status').textContent = `Processing token ${i+1}/${tokens.length}...`; await new Promise(r => setTimeout(r, 300)); }
}
document.getElementById('parallel').onclick = parallel;
document.getElementById('serial').onclick = serial;
draw();
""",
    )


def kv_cache():
    return base(
        "Why KV Cache Exists",
        '<p>Reuse previous key/value tensors when generating the next token.</p>'
        '<div class="controls"><button id="generate">Generate next token</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">The KV cache avoids recomputing keys and values.</div>',
        """
let cache = [];
const tokens = ['The','cat','sat'];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('KV Cache', 40, 30);
  cache.forEach((c, i) => {
    ctx.fillStyle = '#c8e6c9'; ctx.fillRect(40 + i * 90, 50, 80, 120); ctx.strokeRect(40 + i * 90, 50, 80, 120);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(c.token, 80 + i * 90, 80); ctx.fillText('K', 80 + i * 90, 110); ctx.fillText('V', 80 + i * 90, 140);
  });
  ctx.fillStyle = '#90caf9'; ctx.fillRect(40 + cache.length * 90, 50, 80, 120); ctx.strokeRect(40 + cache.length * 90, 50, 80, 120);
  ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('new token', 80 + cache.length * 90, 110);
}
document.getElementById('generate').onclick = () => {
  const next = tokens[cache.length] || 'next';
  cache.push({token: next});
  document.getElementById('status').textContent = `Cached K/V for "${next}". Only the new token is computed.`;
  draw();
};
draw();
""",
    )


def quantization():
    return base(
        "Why Quantization Exists",
        '<p>Reduce precision to save space with small accuracy loss.</p>'
        '<div class="controls"><input id="bits" type="range" min="1" max="8" value="4"><span id="bitsLabel">4 bits</span></div>'
        '<canvas id="c" width="500" height="200"></canvas>'
        '<div id="status">Fewer bits per weight means smaller models.</div>',
        """
const weights = [0.12, 0.87, -0.34, 0.56, -0.91, 0.23, 0.45, -0.66];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function quantize(v, bits) { const levels = Math.pow(2, bits) - 1; return Math.round(v * levels) / levels; }
function draw() {
  const bits = parseInt(document.getElementById('bits').value);
  document.getElementById('bitsLabel').textContent = bits + ' bits';
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  weights.forEach((w, i) => {
    const q = quantize(w, bits);
    ctx.fillStyle = '#90caf9'; ctx.fillRect(40 + i * 55, 100 - w * 80, 40, w * 80); ctx.strokeRect(40 + i * 55, 100 - w * 80, 40, w * 80);
    ctx.fillStyle = '#ef5350'; ctx.fillRect(40 + i * 55, 100 - q * 80, 40, q * 80);
    ctx.fillStyle = '#333'; ctx.font = '10px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(q.toFixed(2), 60 + i * 55, 140);
  });
}
document.getElementById('bits').oninput = draw;
draw();
""",
    )


def tensor_parallelism():
    return base(
        "Why Tensor Parallelism Exists",
        '<p>Split a weight matrix across two GPUs.</p>'
        '<div class="controls"><button id="split">Split matrix</button><button id="reset">Reset</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Tensor parallelism lets a model exceed one GPU.</div>',
        """
let split = false;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!split) {
    ctx.fillStyle = '#e3f2fd'; ctx.fillRect(180, 60, 240, 120); ctx.strokeRect(180, 60, 240, 120);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('Weight matrix', 300, 125);
  } else {
    ctx.fillStyle = '#c8e6c9'; ctx.fillRect(60, 60, 200, 120); ctx.strokeRect(60, 60, 200, 120);
    ctx.fillStyle = '#ffcc80'; ctx.fillRect(340, 60, 200, 120); ctx.strokeRect(340, 60, 200, 120);
    ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('GPU 0', 160, 125); ctx.fillText('GPU 1', 440, 125);
  }
}
document.getElementById('split').onclick = () => { split = true; document.getElementById('status').textContent = 'Matrix split across two GPUs.'; draw(); };
document.getElementById('reset').onclick = () => { split = false; draw(); };
draw();
""",
    )


def moe():
    return base(
        "Why MoE Exists",
        '<p>Route each token to only a subset of experts.</p>'
        '<div class="controls"><button id="route">Route token</button></div>'
        '<canvas id="c" width="600" height="260"></canvas>'
        '<div id="status">MoE activates only the relevant experts per token.</div>',
        """
const experts = ['Syntax','Facts','Math','Code'];
let activeExperts = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw(token) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#90caf9'; ctx.fillRect(260, 30, 80, 40); ctx.strokeRect(260, 30, 80, 40); ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(token || 'token', 300, 55);
  experts.forEach((e, i) => {
    const on = activeExperts.includes(i);
    ctx.fillStyle = on ? '#c8e6c9' : '#e0e0e0';
    ctx.fillRect(80 + i * 130, 140, 100, 60); ctx.strokeRect(80 + i * 130, 140, 100, 60);
    ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(e, 130 + i * 130, 175);
    if (on) { ctx.beginPath(); ctx.moveTo(300, 70); ctx.lineTo(130 + i * 130, 140); ctx.strokeStyle = '#66bb6a'; ctx.stroke(); ctx.strokeStyle = '#000'; }
  });
}
document.getElementById('route').onclick = () => {
  const tokens = ['2+2','Paris','def','hello'];
  const token = tokens[Math.floor(Math.random() * tokens.length)];
  activeExperts = [Math.floor(Math.random() * experts.length)];
  document.getElementById('status').textContent = `Token "${token}" routed to ${experts[activeExperts[0]]}.`;
  draw(token);
};
draw('');
""",
    )


def inference_servers():
    return base(
        "Why Inference Servers Exist",
        '<p>Batch incoming requests to keep the GPU saturated.</p>'
        '<div class="controls"><button id="arrive">New request</button><button id="batch">Run batch</button></div>'
        '<canvas id="c" width="600" height="220"></canvas>'
        '<div id="status">Batching increases throughput and reduces per-request latency.</div>',
        """
let queue = [];
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#333'; ctx.font = '14px sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Request queue', 40, 30);
  queue.forEach((r, i) => {
    ctx.fillStyle = '#90caf9'; ctx.fillRect(40 + i * 70, 50, 60, 40); ctx.strokeRect(40 + i * 70, 50, 60, 40);
    ctx.fillStyle = '#333'; ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(r, 70 + i * 70, 74);
  });
  ctx.fillStyle = '#c8e6c9'; ctx.fillRect(40, 140, 520, 50); ctx.strokeRect(40, 140, 520, 50);
  ctx.fillStyle = '#333'; ctx.font = '16px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('GPU batch', 300, 170);
}
document.getElementById('arrive').onclick = () => { if (queue.length < 8) queue.push('req' + (queue.length+1)); draw(); };
document.getElementById('batch').onclick = () => {
  const batch = queue.splice(0, Math.min(queue.length, 4));
  document.getElementById('status').textContent = `Ran batch of ${batch.length} requests together.`;
  draw();
};
draw();
""",
    )


SIMULATIONS = {
    1: counting,
    2: number_memory,
    3: arrays,
    4: memory_addresses,
    5: copying_expensive,
    6: locality,
    7: linear_search,
    8: ordering_helps,
    9: binary_search,
    10: trees_exist,
    11: balancing_exists,
    12: hashing_exists,
    13: sorting_exists,
    14: divide_conquer,
    15: dynamic_programming,
    16: greedy,
    17: graphs,
    18: functions,
    19: recursion,
    20: stacks,
    21: queues,
    22: schedulers,
    23: processes,
    24: threads,
    25: locks,
    26: deadlocks,
    27: virtual_memory,
    28: context_switching,
    29: files_arent_enough,
    30: indexes_exist,
    31: btrees_won,
    32: transactions,
    33: mvcc,
    34: query_planners,
    35: computers_need_addresses,
    36: packets_exist,
    37: tcp_exists,
    38: congestion,
    39: load_balancers,
    40: one_computer,
    41: clocks_lie,
    42: consensus,
    43: raft,
    44: eventual_consistency,
    45: distributed_transactions,
    46: caches_exist,
    47: cdns,
    48: message_queues,
    49: sharding,
    50: replication,
    51: search_engines,
    52: gpus,
    53: matmul,
    54: attention,
    55: transformers_scale,
    56: kv_cache,
    57: quantization,
    58: tensor_parallelism,
    59: moe,
    60: inference_servers,
}


def get_simulation_html(chapter_num, title, idea):
    fn = SIMULATIONS.get(chapter_num)
    if fn:
        return fn()
    return base(
        title,
        f'<p>Interactive simulation for: {title}</p><canvas id="c" width="600" height="200"></canvas><div id="status">{idea}</div>',
        'const canvas = document.getElementById("c"); const ctx = canvas.getContext("2d"); ctx.fillText("Simulation placeholder", 50, 50);',
    )
