import React from "react";
import { useNavigate } from "react-router-dom";
import "../styles/MainPage.css";

const MainPage = () => {
  const navigate = useNavigate();

  return (
    <div className="main-container">
      <h1 className="main-title">당신의 꿈을 응원한다</h1>
      <button className="main-button" onClick={() => navigate("/search")}>
        채용공고검색엔진
      </button>
    </div>
  );
};

export default MainPage;
