/**
 * SpeakerIdentification Component
 * 
 * A component for selecting and identifying speakers in court proceedings.
 * Displays buttons for each known speaker and allows selection.
 */

import React, { useState } from 'react';
import { FaUserPlus } from 'react-icons/fa';
import './SpeakerIdentification.css';

const SpeakerIdentification = ({ 
  speakers, 
  currentSpeaker, 
  onSpeakerChange,
  disabled = false
}) => {
  const [showAddSpeaker, setShowAddSpeaker] = useState(false);
  const [newSpeaker, setNewSpeaker] = useState({
    name: '',
    role: '',
    id: ''
  });
  
  // Default speaker roles with colors if not provided
  const defaultSpeakers = [
    { id: 'judge-01', name: 'Judge', role: 'judge', color: '#4a7ba7' },
    { id: 'prosecutor-01', name: 'Prosecutor', role: 'prosecutor', color: '#6b486b' },
    { id: 'defense-01', name: 'Defense', role: 'defense', color: '#7b6888' },
    { id: 'witness-01', name: 'Witness', role: 'witness', color: '#a05d56' },
    { id: 'defendant-01', name: 'Defendant', role: 'defendant', color: '#d0743c' },
    { id: 'clerk-01', name: 'Court Clerk', role: 'clerk', color: '#5aae61' }
  ];
  
  // Combine provided speakers with defaults, removing duplicates by role
  const allSpeakers = () => {
    const providedRoles = speakers.map(s => s.role);
    const filteredDefaults = defaultSpeakers.filter(s => !providedRoles.includes(s.role));
    return [...speakers, ...filteredDefaults];
  };
  
  // Handle speaker selection
  const handleSelectSpeaker = (speaker) => {
    if (disabled) return;
    onSpeakerChange(speaker);
  };
  
  // Toggle add speaker form
  const toggleAddSpeakerForm = () => {
    setShowAddSpeaker(!showAddSpeaker);
  };
  
  // Handle new speaker form changes
  const handleNewSpeakerChange = (e) => {
    const { name, value } = e.target;
    setNewSpeaker({ ...newSpeaker, [name]: value });
  };
  
  // Add new speaker
  const handleAddSpeaker = (e) => {
    e.preventDefault();
    
    if (!newSpeaker.name || !newSpeaker.role) {
      alert('Name and role are required');
      return;
    }
    
    // Generate a new unique ID
    const id = `${newSpeaker.role}-${Date.now()}`;
    
    // Generate a random color
    const getRandomColor = () => {
      const letters = '0123456789ABCDEF';
      let color = '#';
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    };
    
    const newSpeakerObject = {
      ...newSpeaker,
      id,
      color: getRandomColor()
    };
    
    // Call parent function to add speaker to the list
    if (typeof onAddSpeaker === 'function') {
      onAddSpeaker(newSpeakerObject);
    }
    
    // Select the new speaker
    onSpeakerChange(newSpeakerObject);
    
    // Reset form and hide it
    setNewSpeaker({ name: '', role: '', id: '' });
    setShowAddSpeaker(false);
  };
  
  return (
    <div className="speaker-identification">
      <div className="speaker-label">
        <span>Current Speaker:</span>
        {currentSpeaker ? (
          <span className="current-speaker-name" style={{ color: currentSpeaker.color }}>
            {currentSpeaker.name} ({currentSpeaker.role})
          </span>
        ) : (
          <span className="current-speaker-name no-selection">No speaker selected</span>
        )}
      </div>
      
      <div className="speaker-buttons">
        {allSpeakers().map((speaker) => (
          <button
            key={speaker.id}
            className={`speaker-button ${currentSpeaker?.id === speaker.id ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            style={{ 
              borderColor: speaker.color,
              backgroundColor: currentSpeaker?.id === speaker.id ? speaker.color : 'transparent',
              color: currentSpeaker?.id === speaker.id ? 'white' : speaker.color
            }}
            onClick={() => handleSelectSpeaker(speaker)}
            disabled={disabled}
          >
            <span className="speaker-name">{speaker.name}</span>
            <span className="speaker-role">{speaker.role}</span>
          </button>
        ))}
        
        <button 
          className="add-speaker-button"
          onClick={toggleAddSpeakerForm}
          disabled={disabled}
        >
          <FaUserPlus />
          <span>Add Speaker</span>
        </button>
      </div>
      
      {showAddSpeaker && (
        <div className="add-speaker-form">
          <form onSubmit={handleAddSpeaker}>
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input
                type="text"
                id="name"
                name="name"
                value={newSpeaker.name}
                onChange={handleNewSpeakerChange}
                placeholder="Full name"
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="role">Role:</label>
              <select
                id="role"
                name="role"
                value={newSpeaker.role}
                onChange={handleNewSpeakerChange}
                required
              >
                <option value="">Select a role</option>
                <option value="judge">Judge</option>
                <option value="prosecutor">Prosecutor</option>
                <option value="defense">Defense Counsel</option>
                <option value="witness">Witness</option>
                <option value="defendant">Defendant</option>
                <option value="clerk">Court Clerk</option>
                <option value="expert">Expert Witness</option>
                <option value="interpreter">Interpreter</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="form-buttons">
              <button type="submit" className="save-button">Add Speaker</button>
              <button type="button" className="cancel-button" onClick={toggleAddSpeakerForm}>Cancel</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default SpeakerIdentification;
