import React from 'react';
import { Button as MuiButton } from '@mui/material';
import type { ButtonProps } from '@mui/material';

export const Button: React.FC<ButtonProps> = (props) => {
  return <MuiButton {...props} />;
};
