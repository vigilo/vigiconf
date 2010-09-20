
sub searchTrap
{
        my ($map, $key)=@_;

        return ( exists $mapTrap{$map}{$key} ? $mapTrap{$map}{$key} : $key)
}

1;