import React from 'react';

function SimpleApp() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#1a1a1a',
      color: 'white',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>VITA 面试助手</h1>
      <p style={{ fontSize: '1.2rem', marginBottom: '2rem' }}>Virtual Interview & Training Assistant</p>
      <div style={{
        backgroundColor: '#333',
        padding: '2rem',
        borderRadius: '10px',
        textAlign: 'center'
      }}>
        <h2 style={{ marginBottom: '1rem' }}>系统状态检查</h2>
        <p>✅ React 应用已加载</p>
        <p>✅ 组件渲染正常</p>
        <p>✅ 样式应用成功</p>
        <button 
          style={{
            marginTop: '1rem',
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
          onClick={() => alert('按钮点击正常！')}
        >
          测试交互
        </button>
      </div>
    </div>
  );
}

export default SimpleApp;