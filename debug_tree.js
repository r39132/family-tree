// Debug script to clear tree cache and inspect tree data
// Run this in browser console on the family tree page

// Clear tree cache
if (typeof window !== 'undefined' && window.localStorage) {
  const keys = Object.keys(localStorage).filter(key => key.startsWith('tree_cache_'));
  console.log('Clearing tree cache keys:', keys);
  keys.forEach(key => localStorage.removeItem(key));
  console.log('Tree cache cleared. Please refresh the page.');
}

// Inspect current tree structure
console.log('Current tree state:', window.treeData);

// You can also manually inspect the API response
fetch('/api/tree')
  .then(response => response.json())
  .then(data => {
    console.log('Fresh API data:', data);
    console.log('Roots count:', data.roots?.length || 0);
    console.log('Members count:', data.members?.length || 0);
    if (data.roots?.length > 0) {
      console.log('First root:', data.roots[0]);
      console.log('First root children:', data.roots[0].children);
    }
  })
  .catch(error => console.error('Error fetching tree data:', error));
