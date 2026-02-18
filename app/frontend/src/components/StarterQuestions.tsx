import React, { useEffect, useState } from 'react';

interface StarterQuestionsProps {
  onSelectQuestion: (question: string) => void;
}

// Fallback questions if API fails
const DEFAULT_QUESTIONS = [
  "What electricity plans does Alinta Energy offer?",
  "How do I pay my energy bill online?",
  "What is a solar feed-in tariff?",
  "What should I do if I'm moving house?",
  "How can I get help with paying my energy bill?",
];

const StarterQuestions: React.FC<StarterQuestionsProps> = ({ onSelectQuestion }) => {
  const [questions, setQuestions] = useState<string[]>(DEFAULT_QUESTIONS);

  useEffect(() => {
    // Fetch starter questions from API
    fetch('/api/starter-questions')
      .then(res => res.json())
      .then(data => {
        if (data.questions && data.questions.length > 0) {
          setQuestions(data.questions);
        }
      })
      .catch(err => {
        console.error('Failed to fetch starter questions:', err);
        // Use default questions on error
      });
  }, []);

  return (
    <div className="starter-questions">
      {questions.map((question, index) => (
        <button
          key={index}
          onClick={() => onSelectQuestion(question)}
          className="starter-question-button"
        >
          {question}
        </button>
      ))}
    </div>
  );
};

export default StarterQuestions;
