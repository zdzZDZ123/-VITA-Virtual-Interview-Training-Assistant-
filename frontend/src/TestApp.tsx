import React from 'react';

function TestApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>VITA 面试助手测试页面</h1>
      <p>如果你能看到这个页面，说明React应用正在正常运行。</p>
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
        <h2>系统状态</h2>
        <ul>
          <li>✅ React 应用已加载</li>
          <li>✅ 组件渲染正常</li>
          <li>✅ 样式应用成功</li>
        </ul>
      </div>
    </div>
  );
}

export default TestApp;