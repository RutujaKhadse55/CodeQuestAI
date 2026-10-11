class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {target: 0}
        for i, n in enumerate(nums):
            need = target - n
            if need in seen:
                return [seen[need], i]
            seen[n] = i
        return []
