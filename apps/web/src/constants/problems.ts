import { DsaProblem } from "../types";
import ProblemData from '../../../../data/data.json'

export const PROBLEMS: DsaProblem[] = ProblemData.exercises.map((item, index) => {
  return {
    id: index, 
    title: item.title,
    difficulty: item.difficulty,
    topic: "Algorithms", 
    summary: item.exercise,
    template: item.template
  };
})


export const STORAGE_KEY = "dsa:last-problem-id";
export const LANG_STORAGE_KEY = "dsa:last-lang-id";