import React from 'react';

const Explanation = ({ percepts, reason }) => {
  return (
    <div>
      <h3>Move Explanation:</h3>
      <pre style={{ whiteSpace: 'pre-wrap', background: '#f8f8f8', padding: 10, borderRadius: 4 }}>{reason}</pre>
      <h4>Percepts:</h4>
      <ul>
        {percepts && percepts.map((p, idx) => <li key={idx}>{p}</li>)}
      </ul>
    </div>
  );
};

export default Explanation;
