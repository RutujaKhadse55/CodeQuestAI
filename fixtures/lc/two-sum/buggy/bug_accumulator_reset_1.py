class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        for i, n in enumerate(nums):
            seen = {}
            need = target - n
            if need in seen:
                return [seen[need], i]
            seen[n] = i
        return []
