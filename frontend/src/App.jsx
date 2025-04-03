// App.jsx

"use client"

import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Order from './components/Order';  // Import the Order component here

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Order />} />  {/* Make sure the path renders the Order component */}
        {/* You can add other routes here as needed */}
      </Routes>
    </Router>
  )
}

export default App;
