class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, n in enumerate(nums):
            need = n - target
            if need in seen:
                return [seen[need], i]
            seen[n] = i
        return []
