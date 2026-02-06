import type { MatchAnalysis as MatchAnalysisType } from "../api";
import "./MatchAnalysis.css";

interface Props {
  data: MatchAnalysisType;
}

export function MatchAnalysis({ data }: Props) {
  const { match_score, strengths, gaps, key_insights, skill_overlap, missing_skills } = data;
  const score = Math.max(0, Math.min(100, Number(match_score) || 0));

  return (
    <div className="match-analysis">
      <div className="match-score">
        <div className="score-ring" style={{ ["--p" as never]: score }}>
          <div className="score-ring-inner">
            <span className="score-value">{score}%</span>
            <span className="score-label">Match</span>
          </div>
        </div>
        <div className="score-sub">
          <span><strong>{skill_overlap.length}</strong> overlapping skills</span>
          <span>•</span>
          <span><strong>{missing_skills.length}</strong> missing skills</span>
        </div>
      </div>

      <div className="analysis-grid">
        <div className="analysis-block strengths">
          <h3>Strengths</h3>
          <ul>
            {strengths.length ? strengths.map((s, i) => (
              <li key={i}>{s}</li>
            )) : <li className="empty">None identified</li>}
          </ul>
        </div>
        <div className="analysis-block gaps">
          <h3>Gaps</h3>
          <ul>
            {gaps.length ? gaps.map((s, i) => (
              <li key={i}>{s}</li>
            )) : <li className="empty">None identified</li>}
          </ul>
        </div>
      </div>

      <div className="analysis-block insights">
        <h3>Key Insights</h3>
        <ul>
          {key_insights.length ? key_insights.map((s, i) => (
            <li key={i}>{s}</li>
          )) : <li className="empty">None</li>}
        </ul>
      </div>

      {(skill_overlap.length > 0 || missing_skills.length > 0) && (
        <div className="skills-row">
          <div className="skills-block">
            <h3>Skill Overlap</h3>
            <div className="skill-tags">
              {skill_overlap.map((s, i) => (
                <span key={i} className="tag tag-success">{s}</span>
              ))}
            </div>
          </div>
          <div className="skills-block">
            <h3>Missing Skills</h3>
            <div className="skill-tags">
              {missing_skills.map((s, i) => (
                <span key={i} className="tag tag-danger">{s}</span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
