import { DsaProblem, MentorMode } from "../types";

export const MODES: MentorMode[] = ["explain", "interview", "hints-only"];

export const PROBLEMS: DsaProblem[] = [
  {
    id: "two-sum",
    title: "Two Sum",
    difficulty: "Easy",
    topic: "Arrays, Hash Map",
    summary: "Find two indices whose values add up to a target in linear time."
  },
  {
    id: "valid-parentheses",
    title: "Valid Parentheses",
    difficulty: "Easy",
    topic: "Stack",
    summary: "Validate bracket order using stack pushes and pops."
  },
  {
    id: "longest-substring-no-repeat",
    title: "Longest Substring Without Repeating Characters",
    difficulty: "Medium",
    topic: "Sliding Window",
    summary: "Use two pointers and a seen map to maintain a valid unique window."
  },
  {
    id: "merge-k-sorted-lists",
    title: "Merge k Sorted Lists",
    difficulty: "Hard",
    topic: "Heap, Linked List",
    summary: "Merge multiple sorted linked lists efficiently with a min heap."
  }
];

export const STORAGE_KEY = "dsa:last-problem-id";
