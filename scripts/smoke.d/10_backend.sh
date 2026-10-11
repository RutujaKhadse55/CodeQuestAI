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
