/* eslint-env jest */
import React from 'react';
import { Image } from 'react-native';
import { render, screen } from '@testing-library/react-native';
import PosterImage from '../../components/PosterImage';

describe('PosterImage', () => {
  it('renders an Image from the given URL', () => {
    render(<PosterImage url="https://img/poster.jpg" />);

    const image = screen.UNSAFE_getByType(Image);
    expect(image.props.source).toEqual({ uri: 'https://img/poster.jpg' });
  });

  it('falls back to a placeholder glyph when the URL is missing', () => {
    render(<PosterImage url={null} />);

    // No Image is mounted; the em-dash placeholder stands in.
    expect(screen.UNSAFE_queryByType(Image)).toBeNull();
    expect(screen.getByText('—')).toBeOnTheScreen();
  });
});
