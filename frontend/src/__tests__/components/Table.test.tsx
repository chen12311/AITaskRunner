/**
 * Table Component Tests
 * 测试 Table 组件
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from '@/components/ui/table'

describe('Table', () => {
  it('should render basic table structure', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
  })

  it('should render table with multiple rows', () => {
    const data = [
      { id: 1, name: 'Alice', email: 'alice@example.com' },
      { id: 2, name: 'Bob', email: 'bob@example.com' },
      { id: 3, name: 'Charlie', email: 'charlie@example.com' },
    ]

    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.id}>
              <TableCell>{row.id}</TableCell>
              <TableCell>{row.name}</TableCell>
              <TableCell>{row.email}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    )

    expect(screen.getAllByRole('row')).toHaveLength(4) // 1 header + 3 body rows
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('Charlie')).toBeInTheDocument()
  })

  it('should render table with footer', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Item</TableHead>
            <TableHead>Price</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Product A</TableCell>
            <TableCell>$10</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Total</TableCell>
            <TableCell>$10</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    )

    expect(screen.getByText('Total')).toBeInTheDocument()
  })

  it('should render table with caption', () => {
    render(
      <Table>
        <TableCaption>A list of users</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>User 1</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByText('A list of users')).toBeInTheDocument()
  })

  it('should apply custom className to table', () => {
    render(
      <Table className="custom-table-class">
        <TableBody>
          <TableRow>
            <TableCell>Content</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('table')).toHaveClass('custom-table-class')
  })

  it('should apply custom className to TableHeader', () => {
    render(
      <Table>
        <TableHeader className="custom-header-class">
          <TableRow>
            <TableHead>Header</TableHead>
          </TableRow>
        </TableHeader>
      </Table>
    )

    const thead = screen.getByRole('rowgroup')
    expect(thead).toHaveClass('custom-header-class')
  })

  it('should apply custom className to TableRow', () => {
    render(
      <Table>
        <TableBody>
          <TableRow className="custom-row-class">
            <TableCell>Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('row')).toHaveClass('custom-row-class')
  })

  it('should apply custom className to TableCell', () => {
    render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell className="custom-cell-class">Cell Content</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('cell')).toHaveClass('custom-cell-class')
  })

  it('should apply custom className to TableHead', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="custom-head-class">Header</TableHead>
          </TableRow>
        </TableHeader>
      </Table>
    )

    expect(screen.getByRole('columnheader')).toHaveClass('custom-head-class')
  })

  it('should render empty table body', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell colSpan={1} className="text-center">
              No data available
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('should render table with data-state attribute on selected row', () => {
    render(
      <Table>
        <TableBody>
          <TableRow data-state="selected">
            <TableCell>Selected Row</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('row')).toHaveAttribute('data-state', 'selected')
  })

  it('should have proper data-slot attributes', () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Header</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    )

    expect(screen.getByRole('table')).toHaveAttribute('data-slot', 'table')
    expect(screen.getByRole('columnheader')).toHaveAttribute('data-slot', 'table-head')
    expect(screen.getByRole('cell')).toHaveAttribute('data-slot', 'table-cell')
  })
})
