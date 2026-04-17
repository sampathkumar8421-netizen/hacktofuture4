import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatRoom from './pages/ChatRoom';
import Dashboard from './pages/Dashboard';
import DataOps from './pages/DataOps';

function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<ChatRoom />} />
          <Route path="/analysis" element={<Dashboard />} />
          <Route path="/data-ops" element={<DataOps />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
