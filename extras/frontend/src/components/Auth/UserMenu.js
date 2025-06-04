import React from 'react';
import { useAuth } from '../../context/AuthContext';
import './UserMenu.css';

const UserMenu = () => {
  const { user, signOut } = useAuth();
  
  const username = user?.username || user?.attributes?.email || 'User';
  
  return (
    <div className="user-menu">
      <span className="username">Hello, {username}</span>
      <button onClick={signOut} className="signout-button">
        Sign Out
      </button>
    </div>
  );
};

export default UserMenu; 