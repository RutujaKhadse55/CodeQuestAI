# [BE] Phase 1 smoke: auth, capture fixtures, analyze v0 on a correct solution, attack set blocked.
test "$(curl -s -o /dev/null -w '%{http_code}' "$B/health")" = 401
UID_=$(curl -sf -H "$H" -XPOST "$B/users" | sed 's/.*"user_id":"\([^"]*\)".*/\1/')
test -n "$UID_"
for slug in two-sum binary-search maximum-subarray; do
  curl -sf -H "$H" -H "$J" -XPOST "$B/problems/capture" -d @"fixtures/lc/$slug/problem.json" | grep -q '"supported":true'
done
CODE='class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, n in enumerate(nums):\n            if target - n in seen:\n                return [seen[target - n], i]\n            seen[n] = i\n'
curl -sf -H "$H" -H "$J" -XPOST "$B/analyze" -d "{\"user_id\":\"$UID_\",\"problem_slug\":\"two-sum\",\"code\":\"$CODE\"}" | grep -q '"outcome":"passed"'
curl -sf -H "$H" "$B/admin/attacks" | python -c "import sys,json; d=json.load(sys.stdin); assert d['blocked']==d['total']>=7, d"
# Phase 2: an example-passing bug (single-element binary search) must be caught by fuzz, class only, no inputs.
BUG='class Solution:\n    def search(self, nums, target):\n        lo, hi = 0, len(nums) - 1\n        while lo < hi:\n            mid = (lo + hi) // 2\n            if nums[mid] == target: return mid\n            if nums[mid] < target: lo = mid + 1\n            else: hi = mid - 1\n        return -1\n'
curl -sf -H "$H" -H "$J" -XPOST "$B/analyze" -d "{\"user_id\":\"$UID_\",\"problem_slug\":\"binary-search\",\"code\":\"$BUG\"}" \
  | python -c "import sys,json; d=json.load(sys.stdin); f=[r for r in d['results'] if r['kind']=='fuzz'][0]; assert f['outcome']=='wrong_output' and f['failure_class']=='single_element' and f['input'] is None, d"
curl -sf -H "$H" "$B/hint-state/$UID_/binary-search" | grep -q '"allowed_level"'
curl -sf -H "$H" "$B/dashboard/$UID_" | grep -q '"mistakes"'
# Phase 3: recommend + localised error + delete-all
curl -sf -H "$H" "$B/recommend/$UID_" | grep -q '"slug"'
curl -s -H "X-Lang: hi" "$B/health" | grep -q 'errors.UNAUTHORIZED'
curl -sf -H "$H" -XDELETE "$B/users/$UID_/data" | grep -q '"deleted"'
