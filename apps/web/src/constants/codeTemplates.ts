import { CodeLanguage } from "../types";

export const CODE_LANGUAGES: Array<{ id: CodeLanguage; label: string; filename: string }> = [
  { id: "cpp", label: "C++", filename: "main.cpp" },
  { id: "python", label: "Python", filename: "main.py" }
];

export function getStarterCode(language: CodeLanguage): string {
  if (language === "python") {
    return `def solve(nums, target):
    seen = {}

    for index, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], index]
        seen[num] = index

    return []


if __name__ == "__main__":
    print(solve([2, 7, 11, 15], 9))
`;
  }

  return `#include <bits/stdc++.h>
using namespace std;

vector<int> solve(vector<int>& nums, int target) {
    unordered_map<int, int> seen;

    for (int i = 0; i < (int)nums.size(); i++) {
        int complement = target - nums[i];
        if (seen.count(complement)) {
            return {seen[complement], i};
        }
        seen[nums[i]] = i;
    }

    return {};
}

int main() {
    vector<int> nums = {2, 7, 11, 15};
    auto result = solve(nums, 9);

    for (int index : result) {
        cout << index << ' ';
    }
    cout << '\n';
}
`;
}
