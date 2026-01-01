import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getMembers, createMember } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import type { Member } from '../types';
import './UserSelect.css';

const AVATAR_COLORS = ['#E53935', '#8E24AA', '#1E88E5', '#43A047', '#FB8C00', '#00ACC1', '#5E35B1'];

export function UserSelect() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectMember } = useCurrentMember();
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');

  const { data: members, isLoading } = useQuery({
    queryKey: ['members'],
    queryFn: getMembers,
  });

  const addMutation = useMutation({
    mutationFn: (name: string) => createMember({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
      setNewName('');
      setShowAdd(false);
    },
  });

  const handleSelect = (member: Member) => {
    selectMember(member);
    navigate('/swipe');
  };

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (newName.trim()) {
      addMutation.mutate(newName.trim());
    }
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getColor = (index: number) => AVATAR_COLORS[index % AVATAR_COLORS.length];

  if (isLoading) {
    return <div className="user-select loading">Loading...</div>;
  }

  return (
    <div className="user-select">
      <motion.div
        className="hero"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1>Family Flix</h1>
        <p>Who's watching?</p>
      </motion.div>

      <div className="members-grid">
        {members?.map((member, index) => (
          <motion.button
            key={member.id}
            className="member-card"
            onClick={() => handleSelect(member)}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div
              className="avatar"
              style={{ backgroundColor: getColor(index) }}
            >
              {member.avatar_url ? (
                <img src={member.avatar_url} alt={member.name} />
              ) : (
                getInitials(member.name)
              )}
            </div>
            <span className="name">{member.name}</span>
          </motion.button>
        ))}

        <motion.button
          className="member-card add-member"
          onClick={() => setShowAdd(true)}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: (members?.length || 0) * 0.1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div className="avatar add">+</div>
          <span className="name">Add</span>
        </motion.button>
      </div>

      {showAdd && (
        <motion.div
          className="add-modal"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAdd(false)}
        >
          <motion.form
            className="add-form"
            initial={{ scale: 0.8, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleAdd}
          >
            <h2>Add Family Member</h2>
            <input
              type="text"
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <div className="buttons">
              <button type="button" onClick={() => setShowAdd(false)}>Cancel</button>
              <button type="submit" disabled={!newName.trim()}>Add</button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </div>
  );
}
